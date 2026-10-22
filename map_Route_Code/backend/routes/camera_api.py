from fastapi import APIRouter
import time
from database import db

router = APIRouter(prefix="", tags=["Camera"])

@router.post("/update-slots")
def update_slots(data: dict):
    conn = db()
    cur = conn.cursor()
    
    # 1. FORCE camera_id from the top level of the message
    camera_id = data.get("camera_id")
    if not camera_id:
        # Emergency fallback for old nodes, but logs a warning
        if data.get("slots"):
            camera_id = data["slots"][0].get("camera_id")
    
    if not camera_id:
        return {"error": "Missing camera_id. Update your camera node."}

    now = time.time()

    # 2. CLEAR and REPLACE
    # We delete all existing records for this specific camera 
    # and replace them with the current detection results.
    cur.execute("DELETE FROM slots WHERE camera_id = ?", (camera_id,))

    for slot in data["slots"]:
        slot_id = slot.get("slot_id")
        status = slot.get("status", "occupied")
        
        if slot_id:
            cur.execute("""
                INSERT INTO slots (slot_id, camera_id, status, last_seen)
                VALUES (?, ?, ?, ?)
            """, (slot_id, camera_id, status, now))

    conn.commit()
    conn.close()

    return {"message": f"Successfully updated {len(data['slots'])} slots for {camera_id}"}
