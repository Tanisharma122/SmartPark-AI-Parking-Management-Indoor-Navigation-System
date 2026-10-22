# camera_nodes/camera1/main.py
import cv2
import json
import time
import numpy as np
import requests

from config import *
from detector import load_manager
from sender import send_slots  # your existing sender

BACKEND_URL = "http://127.0.0.1:8000"
CAMERA_STATUS_API_KEY = "CAM1-ABC"  # must match backend
CAMERA_STATUS_ID = CAMERA_ID       # same as in config.py


# ---------- SLOT FREE CHECK ----------
def is_free(img, pts):
    mask = np.zeros(img.shape[:2], np.uint8)
    cv2.polylines(mask, [pts], True, 255, 2)
    px = img[mask == 255]

    if len(px) == 0:
        return False

    return (
        np.sum(
            (px[:, 2] > 150) &
            (px[:, 1] < 120) &
            (px[:, 0] < 120)
        ) / len(px)
    ) > 0.45


# ---------- LOAD DATA ----------
with open(SLOTS_JSON, "r") as f:
    slots = json.load(f)

cap = cv2.VideoCapture(VIDEO_PATH)
pm = load_manager(MODEL_PATH, SLOTS_JSON, CONF_THRES, IOU_THRES)

last_send_slots = 0
last_send_status = 0
last_save_frame = 0


# ---------- MAIN LOOP ----------
while True:
    ok, frame = cap.read()
    if not ok:
        break

    frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

    res = pm(frame.copy())
    ref = res.plot_im       # YOLO overlay image
    draw = frame.copy()     # where we draw slots

    free_count = 0
    total_count = len(slots)

    # draw + compute free/occupied one time
    slot_status_list = []
    for s in slots:
        sid = s["slot_id"]
        pts = np.array(s["points"], np.int32)

        free = is_free(ref, pts)
        if free:
            free_count += 1

        color = (0, 255, 0) if free else (0, 0, 255)  # green free, red occupied

        # draw slot
        cv2.polylines(draw, [pts], True, color, 2)

        # draw ID
        cx = int(pts[:, 0].mean())
        cy = int(pts[:, 1].mean())
        cv2.putText(
            draw,
            sid,
            (cx - 10, cy),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 0),
            2,
            cv2.LINE_AA,
        )

        slot_status_list.append({
            "slot_id": sid,
            "status": "free" if free else "occupied",
        })

    occupied_count = total_count - free_count

    # ---------- SEND PER-SLOT DATA TO BACKEND (your existing format) ----------
    payload_slots = {
        "camera_id": CAMERA_ID,
        "slots": slot_status_list,
    }

    now = time.time()

    if now - last_send_slots > SEND_INTERVAL:
        send_slots(payload_slots)  # uses your existing sender.py
        last_send_slots = now

    # ---------- SEND AGGREGATED COUNTS TO BACKEND ----------
    if now - last_send_status > SEND_INTERVAL:
        payload_status = {
            "total_slots": total_count,
            "free_slots": free_count,
            "occupied_slots": occupied_count,
        }
        try:
            resp = requests.post(
                f"{BACKEND_URL}/cameras/{CAMERA_STATUS_ID}/status",
                json=payload_status,
                headers={"X-API-Key": CAMERA_STATUS_API_KEY},
                timeout=2,
            )
            # print("Status sent:", resp.status_code, resp.text)
        except Exception as e:
            print("Error sending counts:", e)
        last_send_status = now

    # ---------- SAVE LATEST FRAME FOR DASHBOARD PREVIEW ----------
    if now - last_save_frame > 1.0:  # save at most once per second
        try:
            cv2.imwrite("latest_cam1.jpg", draw)
        except Exception as e:
            print("Error saving latest frame:", e)
        last_save_frame = now

    # ---------- DISPLAY LOCALLY ----------
    cv2.imshow("Camera 1", draw)
    if cv2.waitKey(1) & 0xFF in [27, ord("q")]:
        break

cap.release()
cv2.destroyAllWindows()
