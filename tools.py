import json

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "send_follow_up_email",
            "description": "Send a follow-up email with Pharmesol product information to the pharmacy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Email address to send the follow-up to",
                    },
                    "pharmacy_name": {
                        "type": "string",
                        "description": "Name of the pharmacy",
                    },
                },
                "required": ["email", "pharmacy_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_callback",
            "description": "Schedule a callback or product demo with the pharmacy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pharmacy_name": {
                        "type": "string",
                        "description": "Name of the pharmacy",
                    },
                    "date_time": {
                        "type": "string",
                        "description": "Preferred date and time for the callback",
                    },
                    "contact_number": {
                        "type": "string",
                        "description": "Phone number to call back on",
                    },
                },
                "required": ["pharmacy_name", "date_time"],
            },
        },
    },
]


def handle_tool_call(name: str, arguments: dict) -> str:
    """Execute a mock tool call and return a confirmation message."""
    if name == "send_follow_up_email":
        email = arguments.get("email", "unknown")
        pharmacy = arguments.get("pharmacy_name", "unknown")
        print(f"\n  [ACTION] Follow-up email sent to {email} for {pharmacy}\n")
        return f"Email successfully sent to {email} for {pharmacy}."

    if name == "schedule_callback":
        pharmacy = arguments.get("pharmacy_name", "unknown")
        date_time = arguments.get("date_time", "TBD")
        contact = arguments.get("contact_number", "on file")
        print(f"\n  [ACTION] Callback scheduled for {pharmacy} at {date_time} (contact: {contact})\n")
        return f"Callback scheduled for {pharmacy} at {date_time}."

    return f"Unknown tool: {name}"
