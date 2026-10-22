from fastapi import APIRouter
from database import db
import time

router = APIRouter()

PRIMARY_CAMERA = "CAM_1"
SECONDARY_CAMERA = "CAM_2"

OFFLINE_TIMEOUT = 3.0   # seconds

@router.get("/active-free-slots")
def active_free_slots():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT camera_id, slot_id, status, last_seen
        FROM slots
    """)
    rows = cur.fetchall()
    conn.close()

    now = time.time()

    cameras = {}

    for cam, slot, status, last_seen in rows:
        if cam not in cameras:
            cameras[cam] = {
                "free": [],
                "last_seen": last_seen
            }

        cameras[cam]["last_seen"] = max(
            cameras[cam]["last_seen"], last_seen
        )

        if status == "free":
            cameras[cam]["free"].append(slot)

    def is_online(cam):
        return cam in cameras and (now - cameras[cam]["last_seen"] < OFFLINE_TIMEOUT)

    cam1_online = is_online(PRIMARY_CAMERA)
    cam2_online = is_online(SECONDARY_CAMERA)

    cam1_free = cameras.get(PRIMARY_CAMERA, {}).get("free", [])
    cam2_free = cameras.get(SECONDARY_CAMERA, {}).get("free", [])

    # 🔥 FINAL CORRECT LOGIC
    if cam1_online and len(cam1_free) > 0:
        active_camera = PRIMARY_CAMERA
        active_slots = cam1_free

    elif cam1_online and len(cam1_free) == 0 and cam2_online:
        active_camera = SECONDARY_CAMERA
        active_slots = cam2_free

    elif not cam1_online and cam2_online:
        active_camera = SECONDARY_CAMERA
        active_slots = cam2_free

    else:
        active_camera = "NONE"
        active_slots = []

    return {
        "active_camera": active_camera,
        "free_slots": active_slots,
        "free_count": len(active_slots),
        "camera_status": {
            "CAM_1": "online" if cam1_online else "offline",
            "CAM_2": "online" if cam2_online else "offline"
        }
    }
