from fastapi import APIRouter
from database import db
import time

router = APIRouter()

@router.post("/update-slots")
def update_slots(data: dict):
    conn = db()
    cur = conn.cursor()

    now = time.time()

    for slot in data["slots"]:
        cur.execute(
            """
            INSERT OR REPLACE INTO slots
            (slot_id, camera_id, status, last_seen)
            VALUES (?, ?, ?, ?)
            """,
            (slot["slot_id"], data["camera_id"], slot["status"], now)
        )

    conn.commit()
    conn.close()

    return {"status": "updated"}
