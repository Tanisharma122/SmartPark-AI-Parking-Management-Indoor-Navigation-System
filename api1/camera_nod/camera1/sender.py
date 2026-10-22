# sender.py
import requests

BACKEND_URL = "http://127.0.0.1:8000"  # change to your backend base URL
SLOTS_API_PATH = "/slots/update"       # adjust to your real endpoint

def send_slots(payload: dict):
    """
    Send per-slot status to your backend.
    Expected payload:
    {
      "camera_id": "cam1",
      "slots": [
        {"slot_id": "P1", "status": "free"},
        ...
      ]
    }
    """
    try:
        resp = requests.post(
            BACKEND_URL + SLOTS_API_PATH,
            json=payload,
            timeout=3,
        )
        print("send_slots:", resp.status_code, resp.text)
    except Exception as e:
        print("Error in send_slots:", e)
