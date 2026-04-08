import structlog
from openai import OpenAI

from backend.config import settings

logger = structlog.get_logger()

SUMMARIZATION_PROMPT = """\
Summarize the following sales conversation concisely. You MUST preserve ALL of these details exactly:

- Any email addresses mentioned, confirmed, or on file
- Any scheduled times, dates, and contact numbers
- Pharmacy name, location, prescription volume, and key details
- What the caller is interested in (demos, pricing, specific features, etc.)
- Any commitments made by either party
- Actions already taken (emails sent, demos scheduled, callbacks booked)
- Any objections or concerns raised by the caller

If a prior summary exists, incorporate it — nothing should ever be lost.

Prior summary: {prior_summary}

Conversation to summarize:
{conversation}

Write a concise but complete summary preserving every detail listed above."""


class ContextManager:
    """Manages conversation context via incremental summarization.

    Instead of a sliding window (which loses information), older messages are
    summarized by the fast model. Critical details — emails, scheduled times,
    pharmacy info, commitments — are explicitly preserved in the summary.
    The summary is injected as a system message so the agent retains full context.
    """

    def __init__(self, client: OpenAI):
        self.client = client
        self.summary: str | None = None

    def maybe_summarize(self, messages: list[dict]) -> list[dict]:
        """If conversation is long enough, summarize older messages and restructure."""
        non_system = [m for m in messages if m.get("role") != "system"]

        if len(non_system) < settings.context_summary_threshold:
            return messages

        logger.info(
            "context.summarization_triggered",
            total_messages=len(messages),
            non_system_count=len(non_system),
        )

        # Separate system messages and conversation messages
        system_msgs = [m for m in messages if m.get("role") == "system"]
        # Keep the original system prompt (first one), drop old summaries
        system_prompt = system_msgs[0] if system_msgs else {"role": "system", "content": ""}

        preserve_count = settings.context_preserve_recent
        to_summarize = non_system[:-preserve_count]
        to_keep = non_system[-preserve_count:]

        self.summary = self._generate_summary(to_summarize)

        summary_msg = {
            "role": "system",
            "content": f"<conversation_summary>\n{self.summary}\n</conversation_summary>",
        }

        new_messages = [system_prompt, summary_msg] + to_keep

        logger.info(
            "context.summarization_complete",
            messages_summarized=len(to_summarize),
            messages_kept=len(to_keep),
            new_total=len(new_messages),
        )

        return new_messages

    def _generate_summary(self, messages: list[dict]) -> str:
        """Use the fast model to summarize conversation history."""
        convo_lines = []
        for m in messages:
            role = m.get("role", "unknown").upper()
            content = m.get("content")
            if content:
                convo_lines.append(f"{role}: {content}")
            elif m.get("tool_calls"):
                tool_names = [tc.get("function", {}).get("name", "?")
                              if isinstance(tc, dict)
                              else getattr(tc.function, "name", "?")
                              for tc in m["tool_calls"]]
                convo_lines.append(f"{role}: [called tools: {', '.join(tool_names)}]")

        conversation_text = "\n".join(convo_lines)
        prior = self.summary or "None"

        prompt = SUMMARIZATION_PROMPT.format(
            prior_summary=prior,
            conversation=conversation_text,
        )

        response = self.client.chat.completions.create(
            model=settings.fast_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            timeout=settings.openai_timeout_seconds,
        )
        return response.choices[0].message.content
