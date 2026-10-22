from fastapi import APIRouter
from database import db

router = APIRouter()

@router.get("/free-slots")
def free_slots():
    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT slot_id FROM slots WHERE status='free'")
    rows = [r[0] for r in cur.fetchall()]

    conn.close()

    return {
        "free_count": len(rows),
        "free_slots": rows
    }
