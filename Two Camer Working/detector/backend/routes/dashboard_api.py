# from fastapi import APIRouter
# from database import db

# router = APIRouter()

# @router.get("/free-slots")
# def free_slots():
#     conn = db()
#     cur = conn.cursor()

#     cur.execute("SELECT slot_id FROM slots WHERE status='free'")
#     rows = [r[0] for r in cur.fetchall()]

#     conn.close()

#     return {
#         "free_count": len(rows),
#         "free_slots": rows
#     }

from fastapi import APIRouter
from database import db

router = APIRouter()

@router.get("/free-slots")
def free_slots_by_camera():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT camera_id, slot_id
        FROM slots
        WHERE status = 'free'
        ORDER BY camera_id, slot_id
    """)

    rows = cur.fetchall()
    conn.close()

    result = {}
    for camera_id, slot_id in rows:
        result.setdefault(camera_id, []).append(slot_id)

    return result
