import json
import requests

API_URL = "http://127.0.0.1:8000/register-camera"
API_KEY = "sk_dev_b1"   # device API key

HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

with open("camera_config.json", "r") as f:
    payload = json.load(f)

try:
    r = requests.post(API_URL, json=payload, headers=HEADERS, timeout=5)

    print("Status Code:", r.status_code)

    # ✅ Safely print response
    if r.headers.get("content-type", "").startswith("application/json"):
        print("Response JSON:", r.json())
    else:
        print("Raw Response:", r.text)

except Exception as e:
    print("❌ Request failed:", e)
