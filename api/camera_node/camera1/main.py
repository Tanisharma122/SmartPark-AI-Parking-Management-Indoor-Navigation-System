import time
import random
import requests

BACKEND_URL = "http://127.0.0.1:8000"
CAMERA_ID = "cam1"
API_KEY = "CAM1-ABC"

payload = {
    "total_slots": total_slots,
    "free_slots": free_slots,
    "occupied_slots": occupied_slots,
}

try:
    requests.post(
        f"{BACKEND_URL}/cameras/{CAMERA_ID}/status",
        json=payload,
        headers={"X-API-Key": API_KEY},
        timeout=2,
    )
except Exception as e:
    print("Error sending status:", e)
###
TOTAL_SLOTS = 20

def main():
    while True:
        occupied = random.randint(0, TOTAL_SLOTS)
        free = TOTAL_SLOTS - occupied

        payload = {
            "total_slots": TOTAL_SLOTS,
            "free_slots": free,
            "occupied_slots": occupied
        }

        try:
            resp = requests.post(
                f"{BACKEND_URL}/cameras/{CAMERA_ID}/status",
                json=payload,
                headers={"X-API-Key": API_KEY},
                timeout=5
            )
            print("Sent status:", resp.status_code, resp.text)
        except Exception as e:
            print("Error sending status:", e)

        time.sleep(5)

if __name__ == "__main__":
    main()
