# import cv2
# import json
# import time
# import numpy as np

# from config import *
# from detector import load_manager
# from sender import send_slots   # ✅ CHANGED

# # ---------- SLOT FREE CHECK ----------
# def is_free(img, pts):
#     mask = np.zeros(img.shape[:2], np.uint8)
#     cv2.polylines(mask, [pts], True, 255, 2)
#     px = img[mask == 255]

#     if len(px) == 0:
#         return False

#     return (
#         np.sum(
#             (px[:, 2] > 150) &
#             (px[:, 1] < 120) &
#             (px[:, 0] < 120)
#         ) / len(px)
#     ) > 0.45


# # ---------- LOAD DATA ----------
# with open(SLOTS_JSON, "r") as f:
#     slots = json.load(f)

# cap = cv2.VideoCapture(VIDEO_PATH)
# pm = load_manager(MODEL_PATH, SLOTS_JSON, CONF_THRES, IOU_THRES)

# last_send = 0


# # ---------- MAIN LOOP ----------
# while True:
#     ok, frame = cap.read()
#     if not ok:
#         break

#     frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

#     res = pm(frame.copy())
#     ref = res.plot_im
#     draw = frame.copy()

#     results = []

#     for s in slots:
#         sid = s["slot_id"]
#         pts = np.array(s["points"], np.int32)

#         free = is_free(ref, pts)
#         color = (0, 0, 255) if free else (0, 255, 0)

#         # draw slot
#         cv2.polylines(draw, [pts], True, color, 2)

#         if free:
#             cx = int(pts[:, 0].mean())
#             cy = int(pts[:, 1].mean())
#             cv2.putText(
#                 draw,
#                 sid,
#                 (cx - 10, cy),
#                 cv2.FONT_HERSHEY_SIMPLEX,
#                 0.5,
#                 (0, 0, 255),
#                 2
#             )

#     # ✅ BACKEND PAYLOAD (EXPECTED FORMAT)
#     payload = {
#         "camera_id": CAMERA_ID,
#         "slots": [
#             {
#                 "slot_id": s["slot_id"],
#                 "status": "free" if is_free(ref, np.array(s["points"], np.int32)) else "occupied"
#             }
#             for s in slots
#         ]
#     }

#     # ---------- SEND TO BACKEND ----------
#     if time.time() - last_send > SEND_INTERVAL:
#         send_slots(payload)
#         last_send = time.time()

#     # ---------- DISPLAY ----------
#     cv2.imshow("Camera", draw)

#     if cv2.waitKey(1) & 0xFF in [27, ord('q')]:
#         break


# cap.release()
# cv2.destroyAllWindows()

import cv2
import json
import time
import numpy as np

from config import *
from detector import load_manager
from sender import send_slots


# ===============================
# LOAD VIDEO IDENTITY (STATIC)
# ===============================
try:
    with open("video_config.json", "r") as f:
        vid_cfg = json.load(f)
    VIDEO_PATH = vid_cfg.get("source", "vid4.mp4")
except:
    VIDEO_PATH = "vid4.mp4" # Fallback


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


# ===============================
# LOAD SLOT DEFINITIONS
# ===============================
with open(SLOTS_JSON, "r") as f:
    slots = json.load(f)


# ===============================
# VIDEO + MODEL INIT
# ===============================
cap = cv2.VideoCapture(VIDEO_PATH)
pm = load_manager(MODEL_PATH, SLOTS_JSON, CONF_THRES, IOU_THRES)

last_send = 0
last_reservation_fetch = 0
reserved_slots = []


# ===============================
# MAIN LOOP
# ===============================
while True:
    ok, frame = cap.read()
    if not ok:
        break

    frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

    res = pm(frame.copy())
    ref = res.plot_im
    draw = frame.copy()

    # --- FETCH RESERVATIONS ---
    if time.time() - last_reservation_fetch > 2.0:
        try:
            res = requests.get(f"{BACKEND_URL}/all-slots-status/{VIDEO_ID}", headers={"x-api-key": DEVICE_API_KEY}, timeout=1)
            if res.status_code == 200:
                reserved_slots = [s["slot_id"] for s in res.json().get("slots", []) if s.get("is_reserved")]
        except:
            pass
        last_reservation_fetch = time.time()

    # ---------- DRAW SLOTS ----------
    for s in slots:
        sid = s["slot_id"]
        pts = np.array(s["points"], np.int32)

        free = is_free(ref, pts)
        
        if sid in reserved_slots:
            color = (0, 255, 255) # Yellow for Reserved
            label_color = (0, 150, 150)
        else:
            color = (0, 0, 255) if free else (0, 255, 0)
            label_color = (0, 0, 255) if free else (0, 255, 0)

        cv2.polylines(draw, [pts], True, color, 2)

        if free or sid in reserved_slots:
            cx = int(pts[:, 0].mean())
            cy = int(pts[:, 1].mean())
            cv2.putText(
                draw,
                sid,
                (cx - 10, cy),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                label_color,
                2
            )

    # ===============================
    # BACKEND PAYLOAD
    # ===============================
    payload = {
        "video_id": VIDEO_ID,
        "slots": [
            {
                "slot_id": s["slot_id"],
                "status": (
                    "free"
                    if is_free(ref, np.array(s["points"], np.int32))
                    else "occupied"
                )
            }
            for s in slots
        ]
    }

    # ---------- SEND TO BACKEND ----------
    if time.time() - last_send > SEND_INTERVAL:
        send_slots(payload)
        last_send = time.time()

    # ---------- DISPLAY ----------
    cv2.imshow(f"Video Feed: {VIDEO_ID}", draw)

    if cv2.waitKey(1) & 0xFF in [27, ord('q')]:
        break


cap.release()
cv2.destroyAllWindows()
