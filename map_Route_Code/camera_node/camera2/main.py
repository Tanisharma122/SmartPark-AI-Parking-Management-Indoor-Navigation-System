import cv2
import json
import time
import numpy as np

from config import *
from detector import load_manager
from sender import send_slots   # ✅ CHANGED

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

last_send = 0


# ---------- MAIN LOOP ----------
while True:
    ok, frame = cap.read()
    if not ok:
        break

    frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

    res = pm(frame.copy())
    ref = res.plot_im
    draw = frame.copy()

    results = []

    for s in slots:
        sid = s["slot_id"]
        pts = np.array(s["points"], np.int32)

        free = is_free(ref, pts)
        color = (0, 0, 255) if free else (0, 255, 0)

        # draw slot
        cv2.polylines(draw, [pts], True, color, 2)

        if free:
            cx = int(pts[:, 0].mean())
            cy = int(pts[:, 1].mean())
            cv2.putText(
                draw,
                sid,
                (cx - 10, cy),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                2
            )

    # ✅ BACKEND PAYLOAD (EXPECTED FORMAT)
    payload = {
        "camera_id": CAMERA_ID,
        "slots": [
            {
                "slot_id": s["slot_id"],
                "status": "free" if is_free(ref, np.array(s["points"], np.int32)) else "occupied"
            }
            for s in slots
        ]
    }

    # ---------- SEND TO BACKEND ----------
    if time.time() - last_send > SEND_INTERVAL:
        send_slots(payload)
        last_send = time.time()

    # Save live frame for navigator
    try:
        cv2.imwrite("live.jpg", draw)
    except:
        pass

    # ---------- DISPLAY ----------
    cv2.imshow("Camera", draw)

    if cv2.waitKey(1) & 0xFF in [27, ord('q')]:
        break


cap.release()
cv2.destroyAllWindows()
