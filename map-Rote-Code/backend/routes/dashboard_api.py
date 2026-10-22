from fastapi import APIRouter, Request
from database import db
from fastapi.responses import JSONResponse
from typing import Any
import json
import time

# Custom Response for Pretty Printing & Auto-Refreshing in Browsers
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
        # Force browsers to refresh every 2 seconds
        headers["Refresh"] = "2"
        # Prevent "showing last one" (caching)
        headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        headers["Pragma"] = "no-cache"
        headers["Expires"] = "0"
        super().init_headers(headers)

router = APIRouter(tags=["Dashboard"], default_response_class=PrettyJSONResponse)

# How long until we consider a camera 'offline' and switch
OFFLINE_TIMEOUT = 10.0 

@router.get("/active-free-slots")
def active_free_slots(request: Request):
    org_id = getattr(request.state, "org_id", None)
    if not org_id:
        return {"error": "Org context missing", "slots": []}

    conn = db()
    cur = conn.cursor()
    now = time.time()

    # 1. PRUNE STALE SLOTS (Clean the database of old data first)
    cur.execute("DELETE FROM slots WHERE (? - last_seen) > ?", (now, OFFLINE_TIMEOUT))
    conn.commit()

    # 2. FETCH DATA FOR ALL ONLINE VIDEOS
    cur.execute("""
        SELECT v.video_id, b.name as basement_name, v.last_heartbeat
        FROM videos v
        JOIN basements b ON v.basement_id = b.basement_id
        WHERE b.org_id = ? AND v.is_active = 1 AND (?-v.last_heartbeat) < 10.0
        ORDER BY v.video_id ASC
    """, (org_id, now))
    
    active_videos = cur.fetchall()
    
    if not active_videos:
        conn.close()
        return {
            "org_id": org_id,
            "count": 0,
            "slots": [],
            "reserved_slots": [],
            "active_video": "N/A",
            "online_cameras": 0,
            "message": "All cameras offline"
        }

    all_zones_data = []
    total_free_slots = []
    total_reserved_slots = []
    total_occupied_slots = []
    
    # Track seen slots to prevent duplicates (slot_id + video_id combination)
    seen_slots = set()

    for v_row in active_videos:
        vid = v_row["video_id"]
        # Fetch EVERY slot for this specific video within the freshness window
        cur.execute("""
            SELECT slot_id, status, is_reserved 
            FROM slots 
            WHERE video_id = ? AND (?-last_seen) < 15.0
        """, (vid, now))
        
        s_rows = cur.fetchall()
        zone_total = []
        
        for sr in s_rows:
            clean_id = sr["slot_id"].strip()
            slot_key = (clean_id, vid)  # Unique identifier for this slot
            
            # Skip if we've already seen this slot (prevents duplicates)
            if slot_key in seen_slots:
                continue
            
            seen_slots.add(slot_key)
            
            # Status Priority: Reserved > Occupied > Free
            if sr["is_reserved"] == 1:
                item = {"slot_id": clean_id, "video_id": vid, "status": "reserved"}
                total_reserved_slots.append(item)
            elif sr["status"] == "occupied":
                item = {"slot_id": clean_id, "video_id": vid, "status": "occupied"}
                total_occupied_slots.append(item)
            else:
                item = {"slot_id": clean_id, "video_id": vid, "status": "free"}
                total_free_slots.append(item)
            zone_total.append(item)
        
        all_zones_data.append({
            "video_id": vid,
            "basement": v_row["basement_name"],
            "free_count": len([s for s in zone_total if s["status"] == "free"]),
            "reserved_count": len([s for s in zone_total if s["status"] == "reserved"]),
            "occupied_count": len([s for s in zone_total if s["status"] == "occupied"]),
            "all_slots": zone_total
        })

    # Smart Zone Switching: Find the first zone with at least one free slot
    primary_vid = "N/A"
    for zone in all_zones_data:
        if zone["free_count"] > 0:
            primary_vid = zone["video_id"]
            break
    
    # Fallback to the first online camera if everything is full
    if primary_vid == "N/A" and all_zones_data:
        primary_vid = all_zones_data[0]["video_id"]
    conn.close()

    return {
        "org_id": org_id,
        "active_video": primary_vid,
        "online_cameras": len(all_zones_data),
        "total_free": len(total_free_slots),
        "total_reserved": len(total_reserved_slots),
        "total_occupied": len(total_occupied_slots),
        "zones": all_zones_data,
        "slots": total_free_slots,             # Backward compatibility
        "reserved_slots": total_reserved_slots  # Backward compatibility
    }

@router.get("/all-slots-status/{video_id}")
def get_all_slots_status(video_id: str):
    """
    Returns ALL slots (free, occupied, reserved) with their statuses.
    Used for the Dashboard/Camera View.
    """
    conn = db()
    cur = conn.cursor()
    now = time.time()
    cur.execute("""
        SELECT slot_id, status, is_reserved, reserved_at
        FROM slots
        WHERE video_id = ? AND (?-last_seen) < 10.0
    """, (video_id, now))
    rows = cur.fetchall()
    conn.close()
    
    return {
        "video_id": video_id,
        "slots": [dict(r) for r in rows]
    }

@router.get("/videos-list")
def get_videos_list(request: Request):
    """
    Returns all videos for the organization with their geo-locations.
    Requires ORG API KEY.
    """
    org_id = getattr(request.state, "org_id", None)
    if not org_id:
        return {"error": "Org context missing", "videos": []}

    conn = db()
    cur = conn.cursor()
    now = time.time()
    cur.execute("""
        SELECT v.video_id, v.latitude, v.longitude, b.name as basement_name, v.is_active, v.last_heartbeat
        FROM videos v
        JOIN basements b ON v.basement_id = b.basement_id
        WHERE b.org_id = ?
    """, (org_id,))
    
    rows = cur.fetchall()
    conn.close()

    videos = []
    for r in rows:
        last_seen = r["last_heartbeat"]
        diff = now - last_seen
        status = "Online" if diff < 10 else "Offline"
        
        v_dict = dict(r)
        v_dict["status"] = status
        v_dict["seconds_ago"] = round(diff, 1) if last_seen > 0 else "Never"
        videos.append(v_dict)

    return {
        "org_id": org_id,
        "total_videos": len(videos),
        "videos": videos
    }

@router.get("/camera-health")
def get_camera_health(request: Request):
    """
    Returns the health status (online/offline) of all cameras for an organization.
    Online if last_heartbeat was within 10 seconds.
    """
    org_id = getattr(request.state, "org_id", None)
    if not org_id:
        return {"error": "Org context missing", "cameras": []}

    conn = db()
    cur = conn.cursor()
    now = time.time()
    
    cur.execute("""
        SELECT v.video_id, v.last_heartbeat, b.name as basement_name
        FROM videos v
        JOIN basements b ON v.basement_id = b.basement_id
        WHERE b.org_id = ?
    """, (org_id,))
    
    rows = cur.fetchall()
    conn.close()

    cameras = []
    for r in rows:
        last_seen = r["last_heartbeat"]
        diff = now - last_seen
        status = "Online" if diff < 10 else "Offline" # 10 second threshold
        
        cameras.append({
            "video_id": r["video_id"],
            "basement": r["basement_name"],
            "status": status,
            "last_seen_seconds_ago": round(diff, 1) if last_seen > 0 else "Never"
        })

    return {
        "org_id": org_id,
        "total_cameras": len(cameras),
        "health": cameras
    }
