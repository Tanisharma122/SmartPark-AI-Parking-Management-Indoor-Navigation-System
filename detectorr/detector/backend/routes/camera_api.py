from fastapi import APIRouter
from database import db

router = APIRouter()

@router.post("/update-slots")
def update_slots(data: dict):
    conn = db()
    cur = conn.cursor()

    for slot in data["slots"]:
        cur.execute(
            "INSERT OR REPLACE INTO slots VALUES (?, ?, ?)",
            (slot["slot_id"], data["camera_id"], slot["status"])
        )

    conn.commit()
    conn.close()

    return {"status": "updated"}
