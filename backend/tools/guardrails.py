from typing import Callable

from pydantic import BaseModel

from backend.tools.registry import ToolExecutionContext


def require_email_in_conversation(args: BaseModel, context: ToolExecutionContext) -> str | None:
    """Block send_follow_up_email if the email was never mentioned by the user or found on file."""
    email = getattr(args, "email", "").lower()
    if not email:
        return "Blocked: no email address provided."

    # Check user messages
    for msg in context.messages:
        if msg.get("role") == "user" and email in str(msg.get("content", "")).lower():
            return None

    # Check system prompt (email on file)
    system_msg = context.messages[0].get("content", "") if context.messages else ""
    if email in system_msg.lower():
        return None

    return f"Blocked: email '{email}' was never mentioned by the caller or found on file."


def rate_limit_tool(tool_name: str, max_calls: int) -> Callable:
    """Factory: returns a guardrail that caps per-session tool invocations."""

    def check(args: BaseModel, context: ToolExecutionContext) -> str | None:
        count = context.session_action_counts.get(tool_name, 0)
        if count >= max_calls:
            return (
                f"Blocked: {tool_name} has already been called {count} time(s) "
                f"this session (max {max_calls})."
            )
        return None

    return check
