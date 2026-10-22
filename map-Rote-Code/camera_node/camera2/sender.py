import requests
from config import BACKEND_URL, DEVICE_API_KEY

API_URL = f"{BACKEND_URL}/update-slots"

def send_slots(payload):
    headers = {
        "x-api-key": DEVICE_API_KEY,
        "Content-Type": "application/json"
    }
    try:
        requests.post(
            API_URL,
            json=payload,
            headers=headers,
            timeout=2
        )
    except Exception as e:
        print("❌ Failed to send slots:", e)
