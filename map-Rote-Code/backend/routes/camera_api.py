from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Any
import json
import time
from database import db

# Custom Response for Pretty Printing & Auto-Refresh
class PrettyJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=4,
            separators=(", ", ": "),
        ).encode("utf-8")

    def init_headers(self, headers=None):
        if headers is None:
            headers = {}
        headers["Refresh"] = "2" # Auto-refresh browser every 2 seconds
        headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        super().init_headers(headers)

router = APIRouter(prefix="", tags=["Camera"], default_response_class=PrettyJSONResponse)

@router.post("/update-slots")
def update_slots(data: dict, request: Request):
    """
    DEVICE INGESTION API
    - Requires DEVICE API key
    - Basement ID and Video ID are attached to request.state
    """
    basement_id = getattr(request.state, "basement_id", None)
    if not basement_id:
        raise HTTPException(status_code=403, detail="Basement context missing.")

    conn = db()
    cur = conn.cursor()

    video_id = (data.get("video_id") or data.get("camera_id") or "").strip()
    if not video_id and data.get("slots"):
        first_slot = data["slots"][0]
        video_id = (first_slot.get("video_id") or first_slot.get("camera_id") or "").strip()

    if not video_id:
        conn.close()
        raise HTTPException(status_code=400, detail="video_id missing in payload.")

    locked_video_id = getattr(request.state, "video_id", None)
    if locked_video_id and locked_video_id.strip() != video_id:
        conn.close()
        raise HTTPException(
            status_code=403,
            detail=f"This API key is only authorized for video {locked_video_id}, but you sent data for {video_id}."
        )

    cur.execute("SELECT 1 FROM videos WHERE video_id=? AND basement_id=? AND is_active=1", (video_id, basement_id))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail=f"Video {video_id} not registered for this basement.")

    now = time.time()
    # Update camera health
    cur.execute("UPDATE videos SET last_heartbeat = ? WHERE video_id = ?", (now, video_id))
    
    # 1. Expire old reservations using precise per-slot timeouts
    cur.execute("""
        UPDATE slots 
        SET is_reserved = 0, reserved_at = 0, status = 'free'
        WHERE is_reserved = 1 AND (? - reserved_at) > reservation_timeout
    """, (now,))

    # 2. Get existing slots to preserve reservation info
    cur.execute("SELECT slot_id, status, is_reserved, reserved_at FROM slots WHERE video_id = ?", (video_id,))
    db_slots = {r["slot_id"]: dict(r) for r in cur.fetchall()}

    inserted = 0
    active_slot_ids = []
    
    for slot in data.get("slots", []):
        slot_id = slot.get("slot_id", "").strip()
        status = slot.get("status", "occupied")
        if not slot_id: continue
        active_slot_ids.append(slot_id)

        # Logic for reserved slots
        is_reserved = 0
        reserved_at = 0
        reserved_by = None
        
        if slot_id in db_slots:
            old = db_slots[slot_id]
            is_reserved = old["is_reserved"]
            reserved_at = old["reserved_at"]
            # If it was reserved and camera now sees it as occupied
            if is_reserved == 1 and status == "occupied":
                # Check 20 second conflict rule
                if (now - reserved_at) < 20:
                    # Stolen! Mark as occupied and clear reservation (conflict handled by navigator polling)
                    is_reserved = 0
                    reserved_at = 0
                else:
                    # User likely arrived or car is there. Carry on.
                    # We keep it as is_reserved=1 for the full 90s duration as per "seen occupied in all camera... till 1m30s"
                    pass

        cur.execute("""
            INSERT INTO slots (slot_id, video_id, status, last_seen, is_reserved, reserved_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(slot_id, video_id) DO UPDATE SET
                status = excluded.status,
                last_seen = excluded.last_seen,
                is_reserved = excluded.is_reserved,
                reserved_at = excluded.reserved_at
        """, (slot_id, video_id.strip(), status, now, is_reserved, reserved_at))
        inserted += 1

    # Remove slots that are no longer reported by the camera
    if active_slot_ids:
        placeholders = ', '.join(['?'] * len(active_slot_ids))
        cur.execute(f"DELETE FROM slots WHERE video_id = ? AND slot_id NOT IN ({placeholders})", (video_id, *active_slot_ids))
    else:
        cur.execute("DELETE FROM slots WHERE video_id = ?", (video_id,))

    conn.commit()
    conn.close()

    return {
        "message": "Slots updated successfully",
        "video_id": video_id,
        "basement_id": basement_id,
        "slots_updated": inserted
    }

@router.get("/video-free-slots/{video_id}")
def get_video_free_slots(video_id: str, request: Request):
    """
    Returns only the currently free slots for a specific video.
    """
    conn = db()
    cur = conn.cursor()
    
    cur.execute("SELECT video_id, last_heartbeat FROM videos WHERE video_id=? AND is_active=1", (video_id,))
    vid_data = cur.fetchone()
    if not vid_data:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Video feed {video_id} not found.")

    now = time.time()
    last_seen = vid_data["last_heartbeat"]
    status = "Online" if (now - last_seen) < 10 else "Offline"

    cur.execute("""
        SELECT slot_id, status, is_reserved
        FROM slots 
        WHERE video_id=? AND (status='free' OR status='reserved') AND (?-last_seen) < 10.0
    """, (video_id, now))
    
    rows = cur.fetchall()
    free_slots = [r["slot_id"] for r in rows if r["status"] == "free" and r["is_reserved"] == 0]
    reserved_slots = [r["slot_id"] for r in rows if r["is_reserved"] == 1]
    conn.close()

    return {
        "video_id": video_id,
        "status": status,
        "health": {
            "last_heartbeat": last_seen,
            "seconds_ago": round(now - last_seen, 1) if last_seen > 0 else "Never"
        },
        "count": len(free_slots),
        "free_slots": free_slots,
        "reserved_slots": reserved_slots,
        "last_updated": now
    }
