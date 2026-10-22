import json
import requests

API_URL = "http://127.0.0.1:8000/register-camera"
API_KEY = "sk_dev_b1"

HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

with open("vid4.json") as f:
    payload = json.load(f)

r = requests.post(API_URL, json=payload, headers=HEADERS)
print(r.status_code, r.json())
