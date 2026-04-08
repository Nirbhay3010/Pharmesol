import json
from pathlib import Path
from typing import Literal

import structlog
from pydantic import BaseModel, Field

from backend.config import settings
from backend.tools.registry import ToolRegistry
from backend.tools.guardrails import require_email_in_conversation, rate_limit_tool

logger = structlog.get_logger()

registry = ToolRegistry()


# ------------------------------------------------------------------
# Input models
# ------------------------------------------------------------------

class SendFollowUpEmailInput(BaseModel):
    email: str = Field(description="Confirmed email address to send the follow-up to")
    pharmacy_name: str = Field(description="Name of the pharmacy")
    content_summary: str = Field(description="Brief summary of what the email will contain")


class ScheduleCallbackInput(BaseModel):
    pharmacy_name: str = Field(description="Name of the pharmacy")
    date_time: str = Field(description="The confirmed date and time for the callback")
    contact_number: str | None = Field(default=None, description="Phone number to call back on")


class CheckDemoAvailabilityInput(BaseModel):
    slot_type: Literal["demo", "callback"] = Field(
        description="Whether to check demo slots or callback slots"
    )


# ------------------------------------------------------------------
# Tool implementations
# ------------------------------------------------------------------

@registry.register(
    name="send_follow_up_email",
    description=(
        "Send a follow-up email with Pharmesol product information to the pharmacy. "
        "Only call this AFTER confirming the email address and content with the caller."
    ),
    input_model=SendFollowUpEmailInput,
    guardrails=[
        require_email_in_conversation,
        rate_limit_tool("send_follow_up_email", settings.max_email_sends_per_session),
    ],
)
def send_follow_up_email(args: SendFollowUpEmailInput) -> str:
    logger.info(
        "action.email_sent",
        email=args.email,
        pharmacy=args.pharmacy_name,
        content=args.content_summary[:100],
    )
    return f"Email successfully sent to {args.email} for {args.pharmacy_name}. Content: {args.content_summary}."


@registry.register(
    name="schedule_callback",
    description=(
        "Schedule a callback or product demo with the pharmacy. "
        "Only call this AFTER the caller has chosen a specific time slot and confirmed."
    ),
    input_model=ScheduleCallbackInput,
    guardrails=[
        rate_limit_tool("schedule_callback", settings.max_callbacks_per_session),
    ],
)
def schedule_callback(args: ScheduleCallbackInput) -> str:
    contact = args.contact_number or "on file"
    logger.info(
        "action.callback_scheduled",
        pharmacy=args.pharmacy_name,
        date_time=args.date_time,
        contact=contact,
    )
    return f"Callback scheduled for {args.pharmacy_name} at {args.date_time}."


@registry.register(
    name="check_demo_availability",
    description=(
        "Check available demo or callback time slots. "
        "Call this when the caller expresses interest in scheduling, BEFORE presenting options."
    ),
    input_model=CheckDemoAvailabilityInput,
    guardrails=[],
)
def check_demo_availability(args: CheckDemoAvailabilityInput) -> str:
    availability_path = Path(__file__).parent.parent / "availability.json"
    with open(availability_path) as f:
        data = json.load(f)
    key = "demo_slots" if args.slot_type == "demo" else "callback_slots"
    available = [s for s in data.get(key, []) if s.get("available")]
    return json.dumps({"available_slots": available})
