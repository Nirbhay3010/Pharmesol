import re

BLOCKED_PATTERNS = [
    (
        re.compile(r'\b\d+\s*(mg|mcg|ml|units?)\b', re.IGNORECASE),
        "potential_dosage_info",
    ),
    (
        re.compile(
            r'\b(take|administer|prescribe|dose)\b.*\b(daily|twice|once|every)\b',
            re.IGNORECASE,
        ),
        "potential_medical_advice",
    ),
    (
        re.compile(
            r'\b(guarantee|warranty|promise)\b.*\b(uptime|availability|results|savings)\b',
            re.IGNORECASE,
        ),
        "unauthorized_guarantee",
    ),
]


def check_response(text: str) -> tuple[bool, str | None]:
    """Check model output against safety patterns.

    Returns (is_safe, reason_if_blocked).
    """
    if not text:
        return True, None

    for pattern, reason in BLOCKED_PATTERNS:
        if pattern.search(text):
            return False, reason

    return True, None
