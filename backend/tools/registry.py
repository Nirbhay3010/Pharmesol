import json
import time
from dataclasses import dataclass, field
from typing import Callable
from collections import Counter

import structlog
from pydantic import BaseModel

logger = structlog.get_logger()


@dataclass
class ToolExecutionContext:
    """Passed to guardrails so they can inspect conversation state."""
    messages: list[dict]
    actions_this_turn: list[dict]
    session_action_counts: Counter = field(default_factory=Counter)


class RegisteredTool:
    __slots__ = ("name", "description", "input_model", "handler", "guardrails")

    def __init__(
        self,
        name: str,
        description: str,
        input_model: type[BaseModel],
        handler: Callable[[BaseModel], str],
        guardrails: list[Callable],
    ):
        self.name = name
        self.description = description
        self.input_model = input_model
        self.handler = handler
        self.guardrails = guardrails


class ToolRegistry:
    """Central registry for all agent tools with Pydantic validation and guardrails."""

    def __init__(self):
        self._tools: dict[str, RegisteredTool] = {}

    def register(
        self,
        name: str,
        description: str,
        input_model: type[BaseModel],
        guardrails: list[Callable] | None = None,
    ):
        """Decorator to register a tool function."""
        def decorator(func: Callable[[BaseModel], str]):
            self._tools[name] = RegisteredTool(
                name=name,
                description=description,
                input_model=input_model,
                handler=func,
                guardrails=guardrails or [],
            )
            return func
        return decorator

    def get_openai_schemas(self) -> list[dict]:
        """Generate OpenAI-compatible tool schemas from Pydantic models."""
        schemas = []
        for tool in self._tools.values():
            json_schema = tool.input_model.model_json_schema()
            json_schema.pop("title", None)
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": json_schema,
                },
            })
        return schemas

    def execute(self, name: str, raw_arguments: str, context: ToolExecutionContext) -> str:
        """Validate input, run guardrails, execute tool. Returns result string.

        Errors are returned as JSON strings (not raised) so the model can self-correct.
        """
        tool = self._tools.get(name)
        if not tool:
            logger.warning("tool.unknown", tool_name=name)
            return json.dumps({"error": f"Unknown tool: {name}"})

        # Step 1: Parse and validate via Pydantic
        try:
            parsed = tool.input_model.model_validate_json(raw_arguments)
        except Exception as e:
            logger.warning("tool.validation_failed", tool_name=name, error=str(e))
            return json.dumps({"error": f"Invalid arguments: {str(e)}"})

        # Step 2: Run pre-execution guardrails
        for guardrail in tool.guardrails:
            rejection = guardrail(parsed, context)
            if rejection is not None:
                logger.warning("tool.guardrail_blocked", tool_name=name, reason=rejection)
                return json.dumps({"error": rejection})

        # Step 3: Execute
        start = time.monotonic()
        try:
            result = tool.handler(parsed)
        except Exception as e:
            logger.error("tool.execution_failed", tool_name=name, error=str(e))
            return json.dumps({"error": f"Tool execution failed: {str(e)}"})

        elapsed_ms = round((time.monotonic() - start) * 1000)
        logger.info("tool.executed", tool_name=name, elapsed_ms=elapsed_ms)
        return result
