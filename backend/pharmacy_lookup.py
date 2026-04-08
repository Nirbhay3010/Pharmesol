import requests
import structlog

from backend.config import settings

logger = structlog.get_logger()


def lookup_by_phone(phone: str) -> dict | None:
    """Look up a pharmacy by caller phone number from the mock API."""
    try:
        response = requests.get(settings.pharmacy_api_url, timeout=settings.pharmacy_api_timeout)
        response.raise_for_status()
        pharmacies = response.json()
    except (requests.RequestException, ValueError):
        logger.warning("pharmacy_lookup.failed", phone=phone)
        return None

    for pharmacy in pharmacies:
        if pharmacy.get("phone") == phone:
            # Only treat pharmacies with valid prescription data as known
            prescriptions = pharmacy.get("prescriptions", [])
            if isinstance(prescriptions, list) and prescriptions and isinstance(prescriptions[0], dict):
                pharmacy["rx_volume"] = sum(p.get("count", 0) for p in prescriptions)
                return pharmacy

    return None
