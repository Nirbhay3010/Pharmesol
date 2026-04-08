import json
from collections import Counter

import structlog
from openai import OpenAI, RateLimitError, APITimeoutError, APIConnectionError, InternalServerError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.config import settings
from backend.tools import TOOLS, registry
from backend.context import ContextManager
from backend.output_guardrails import check_response

logger = structlog.get_logger()

RETRYABLE_ERRORS = (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError)

SAFE_FALLBACK = (
    "That's a great question — let me have one of our specialists follow up with you "
    "directly so we can give you the most accurate answer. Can I take down your details?"
)


class SalesAgent:
    """Pharmesol inbound sales agent powered by OpenAI."""

    def __init__(self, system_prompt: str, session_id: str = ""):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.messages: list[dict] = [{"role": "system", "content": system_prompt}]
        self.last_actions: list[dict] = []
        self.session_action_counts: Counter = Counter()
        self.session_id = session_id
        self.context_manager = ContextManager(self.client)

    # ------------------------------------------------------------------
    # OpenAI API wrapper with retry
    # ------------------------------------------------------------------

    def _create_completion(self, *, model: str, stream: bool = False, include_tools: bool = True):
        """Call OpenAI with retry on transient errors."""

        @retry(
            stop=stop_after_attempt(settings.openai_max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=30),
            retry=retry_if_exception_type(RETRYABLE_ERRORS),
            reraise=True,
        )
        def _call():
            kwargs = dict(
                model=model,
                messages=self.messages,
                timeout=settings.openai_timeout_seconds,
                stream=stream,
            )
            if include_tools:
                kwargs["tools"] = TOOLS
            return self.client.chat.completions.create(**kwargs)

        logger.info(
            "openai.call",
            session_id=self.session_id,
            model=model,
            message_count=len(self.messages),
            stream=stream,
        )
        return _call()

    # ------------------------------------------------------------------
    # Tool execution context
    # ------------------------------------------------------------------

    def _build_tool_context(self):
        from backend.tools.registry import ToolExecutionContext
        return ToolExecutionContext(
            messages=self.messages,
            actions_this_turn=self.last_actions,
            session_action_counts=self.session_action_counts,
        )

    # ------------------------------------------------------------------
    # Tool call handling (bounded loop)
    # ------------------------------------------------------------------

    def _handle_tool_calls(self, response, model=None):
        """Process tool calls in a loop until the model produces a text response."""
        if model is None:
            model = settings.fast_model

        iterations = 0

        while response.choices[0].finish_reason == "tool_calls":
            iterations += 1

            if iterations > settings.max_tool_iterations:
                logger.warning(
                    "tool_loop.max_iterations",
                    session_id=self.session_id,
                    iterations=iterations,
                )
                response = self._create_completion(model=model, include_tools=False)
                break

            assistant_message = response.choices[0].message
            self.messages.append(assistant_message)

            for tool_call in assistant_message.tool_calls:
                ctx = self._build_tool_context()
                result = registry.execute(
                    tool_call.function.name,
                    tool_call.function.arguments,
                    ctx,
                )

                # Track actions (skip internal lookups)
                if tool_call.function.name != "check_demo_availability":
                    try:
                        args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        args = {}
                    self.last_actions.append({
                        "tool": tool_call.function.name,
                        "arguments": args,
                        "result": result,
                    })

                # Update session-level action counts
                self.session_action_counts[tool_call.function.name] += 1

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

            response = self._create_completion(model=model)

        return response

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_greeting(self) -> str:
        """Generate the opening greeting (first assistant turn)."""
        response = self._create_completion(model=settings.model)
        greeting = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": greeting})
        return greeting

    def chat(self, user_message: str) -> str:
        """Process a user message and return the agent's response (non-streaming)."""
        self.last_actions = []
        self.messages.append({"role": "user", "content": user_message})
        self.messages = self.context_manager.maybe_summarize(self.messages)

        response = self._create_completion(model=settings.model)
        response = self._handle_tool_calls(response)

        reply = response.choices[0].message.content

        # Output guardrail check
        is_safe, reason = check_response(reply)
        if not is_safe:
            logger.warning("output_guardrail.blocked", session_id=self.session_id, reason=reason)
            reply = SAFE_FALLBACK

        self.messages.append({"role": "assistant", "content": reply})
        return reply

    def chat_stream(self, user_message: str):
        """Process a user message with true streaming.

        Yields dicts: {"token": "..."} for text tokens, {"done": True, "actions": [...]} at end.
        """
        self.last_actions = []
        self.messages.append({"role": "user", "content": user_message})
        self.messages = self.context_manager.maybe_summarize(self.messages)

        iterations = 0

        while True:
            iterations += 1
            if iterations > settings.max_tool_iterations:
                logger.warning("stream_tool_loop.max_iterations", session_id=self.session_id)
                break

            stream = self._create_completion(model=settings.model, stream=True)

            # Accumulate from stream
            tool_calls_acc: dict[int, dict] = {}
            text_parts: list[str] = []
            finish_reason = None

            for chunk in stream:
                choice = chunk.choices[0]
                delta = choice.delta
                finish_reason = choice.finish_reason or finish_reason

                if delta.content:
                    text_parts.append(delta.content)
                    yield {"token": delta.content}

                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        if idx not in tool_calls_acc:
                            tool_calls_acc[idx] = {"id": tc_delta.id, "name": "", "arguments": ""}
                        if tc_delta.function:
                            if tc_delta.function.name:
                                tool_calls_acc[idx]["name"] = tc_delta.function.name
                            if tc_delta.function.arguments:
                                tool_calls_acc[idx]["arguments"] += tc_delta.function.arguments

            if finish_reason == "tool_calls" and tool_calls_acc:
                # Build assistant message with tool calls for history
                tc_list = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["arguments"]},
                    }
                    for tc in tool_calls_acc.values()
                ]
                self.messages.append({"role": "assistant", "content": None, "tool_calls": tc_list})

                for tc in tool_calls_acc.values():
                    ctx = self._build_tool_context()
                    result = registry.execute(tc["name"], tc["arguments"], ctx)

                    if tc["name"] != "check_demo_availability":
                        try:
                            args = json.loads(tc["arguments"])
                        except json.JSONDecodeError:
                            args = {}
                        self.last_actions.append({
                            "tool": tc["name"],
                            "arguments": args,
                            "result": result,
                        })

                    self.session_action_counts[tc["name"]] += 1
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result,
                    })

                continue  # loop back for next completion

            # Text response — done
            final_content = "".join(text_parts)

            # Output guardrail check
            is_safe, reason = check_response(final_content)
            if not is_safe:
                logger.warning("output_guardrail.blocked", session_id=self.session_id, reason=reason)
                yield {"retract": True, "replacement": SAFE_FALLBACK}
                final_content = SAFE_FALLBACK

            self.messages.append({"role": "assistant", "content": final_content})
            break

        yield {"done": True, "actions": self.last_actions}
