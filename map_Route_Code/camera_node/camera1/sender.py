import requests

API_URL = "http://127.0.0.1:8000/update-slots"
API_KEY = "sp_live_3fa85f64a12b9d9a8e5f3c2b1a0d4e6f"

HEADERS = {
    "X-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

def send_slots(payload):
    try:
        requests.post(
            API_URL,
            json=payload,
            headers=HEADERS,
            timeout=2
        )
    except Exception as e:
        print("❌ Failed to send slots:", e)
