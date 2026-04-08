import requests

API_URL = "https://67e14fb758cc6bf785254550.mockapi.io/pharmacies"


def lookup_by_phone(phone: str) -> dict | None:
    """Look up a pharmacy by caller phone number from the mock API."""
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        pharmacies = response.json()
    except (requests.RequestException, ValueError):
        print("[WARN] Could not reach pharmacy API — proceeding as unknown caller.")
        return None

    for pharmacy in pharmacies:
        if pharmacy.get("phone") == phone:
            # Only treat pharmacies with valid prescription data as known
            prescriptions = pharmacy.get("prescriptions", [])
            if isinstance(prescriptions, list) and prescriptions and isinstance(prescriptions[0], dict):
                pharmacy["rx_volume"] = sum(p.get("count", 0) for p in prescriptions)
                return pharmacy

    return None
