from fastapi import APIRouter
from database import db
import time

router = APIRouter(tags=["Dashboard"])

# How long until we consider a camera 'offline' and switch
OFFLINE_TIMEOUT = 5.0 

@router.get("/active-free-slots")
def active_free_slots():
    conn = db()
    cur = conn.cursor()
    now = time.time()

    # Get every free slot that has been updated recently
    cur.execute("""
        SELECT slot_id, camera_id, last_seen 
        FROM slots 
        WHERE status = 'free' 
          AND (? - last_seen) < ?
    """, (now, OFFLINE_TIMEOUT))
    
    rows = cur.fetchall()
    
    # Also check camera activity (even if no free slots) to determine which is 'Active'
    cur.execute("SELECT camera_id, MAX(last_seen) FROM slots GROUP BY camera_id")
    cam_activity = {row[0]: row[1] for row in cur.fetchall()}
    conn.close()

    PRIMARY = "CAM_1"
    SECONDARY = "CAM_2"

    # Separate free slots by camera
    cam1_free = [
        {"slot_id": r[0], "camera_id": r[1]} 
        for r in rows if r[1] == PRIMARY
    ]
    cam2_free = [
        {"slot_id": r[0], "camera_id": r[1]} 
        for r in rows if r[1] == SECONDARY
    ]

    # Check which cameras are online
    cam1_online = (now - cam_activity.get(PRIMARY, 0) < OFFLINE_TIMEOUT)
    cam2_online = (now - cam_activity.get(SECONDARY, 0) < OFFLINE_TIMEOUT)

    # 1. PRIORITY RULES:
    # Always prefer CAM_1 if it is online and has at least one free space.
    if cam1_online and len(cam1_free) > 0:
        display_slots = cam1_free
    
    # 2. If CAM_1 is online but FULL, OR if CAM_1 is offline/missing
    # Then show CAM_2 free slots (if any)
    elif cam2_online and len(cam2_free) > 0:
        display_slots = cam2_free
        
    # 3. Everything is full or offline
    else:
        display_slots = []

    return {
        "count": len(display_slots),
        "slots": display_slots
    }
