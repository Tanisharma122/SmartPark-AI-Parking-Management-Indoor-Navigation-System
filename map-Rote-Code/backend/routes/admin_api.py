from fastapi import APIRouter, Request, HTTPException, Depends
from database import db
import time
import secrets

router = APIRouter(prefix="/admin", tags=["Admin"])

# Helper to generate a unique API key
def generate_key(prefix: str):
    return f"sk_{prefix}_{secrets.token_hex(8)}"

@router.get("/stats")
def get_global_stats():
    """Returns global system stats for Super Admin."""
    conn = db()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM organizations")
    orgs = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM basements")
    basements = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM videos")
    videos = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM videos WHERE (?-last_heartbeat) < 60", (time.time(),))
    active_now = cur.fetchone()[0]
    
    conn.close()
    return {
        "total_organizations": orgs,
        "total_basements": basements,
        "total_cameras": videos,
        "cameras_active_last_min": active_now
    }

@router.get("/organizations")
def list_organizations():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM organizations")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/create-organization")
def create_org(name: str):
    org_id = f"ORG_{secrets.token_hex(3).upper()}"
    conn = db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO organizations (org_id, name) VALUES (?, ?)", (org_id, name))
        # Generate an Org Dashboard Key
        org_key = generate_key("org")
        cur.execute("""
            INSERT INTO api_keys (key, key_type, target_id, owner)
            VALUES (?, 'org', ?, ?)
        """, (org_key, org_id, f"Dashboard for {name}"))
        conn.commit()
        return {"status": "success", "org_id": org_id, "api_key": org_key}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@router.post("/add-basement")
def add_basement(org_id: str, name: str, lat: float = 0.0, lng: float = 0.0):
    b_id = f"BASE_{secrets.token_hex(3).upper()}"
    conn = db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO basements (basement_id, org_id, name, latitude, longitude)
            VALUES (?, ?, ?, ?, ?)
        """, (b_id, org_id, name, lat, lng))
        conn.commit()
        return {"status": "success", "basement_id": b_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@router.post("/add-video")
def add_video(basement_id: str, video_id: str):
    conn = db()
    cur = conn.cursor()
    try:
        # Check if basement exists
        cur.execute("SELECT org_id FROM basements WHERE basement_id=?", (basement_id,))
        res = cur.fetchone()
        if not res:
            raise HTTPException(status_code=404, detail="Basement not found")
        org_id = res["org_id"]

        cur.execute("""
            INSERT OR IGNORE INTO videos (video_id, basement_id, type, is_active)
            VALUES (?, ?, 'video', 1)
        """, (video_id, basement_id))
        
        # Generate a fresh Device Key for this specific video
        device_key = generate_key("dev")
        cur.execute("""
            INSERT INTO api_keys (key, key_type, target_id, owner)
            VALUES (?, 'device', ?, ?)
        """, (device_key, video_id, f"Camera {video_id}"))
        
        conn.commit()
        return {"status": "success", "video_id": video_id, "device_api_key": device_key}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@router.delete("/delete-organization/{org_id}")
def delete_org(org_id: str):
    """Deletes an organization and ALL associated data (basements, videos, keys)."""
    conn = db()
    cur = conn.cursor()
    try:
        # Normalize input
        org_id = org_id.strip().upper()

        # 1. Get all basement IDs for this org
        cur.execute("SELECT basement_id FROM basements WHERE UPPER(TRIM(org_id)) = ?", (org_id,))
        basements = [r["basement_id"] for r in cur.fetchall()]
        
        # 2. Get all video IDs for those basements
        videos = []
        for b_id in basements:
            cur.execute("SELECT video_id FROM videos WHERE UPPER(TRIM(basement_id)) = UPPER(TRIM(?))", (b_id,))
            videos.extend([r["video_id"] for r in cur.fetchall()])

        # 3. Cascaded Deletion
        # Delete slots for all videos
        for v_id in videos:
            cur.execute("DELETE FROM slots WHERE UPPER(TRIM(video_id)) = UPPER(TRIM(?))", (v_id,))
        
        # Delete videos
        for b_id in basements:
            cur.execute("DELETE FROM videos WHERE UPPER(TRIM(basement_id)) = UPPER(TRIM(?))", (b_id,))
            
        # Delete basements
        cur.execute("DELETE FROM basements WHERE UPPER(TRIM(org_id)) = ?", (org_id,))
        
        # Delete API keys (we need to find them first because they don't have org_id directly anymore)
        # Actually we can just delete keys where target_id IN (org_id, basement_ids, video_ids)
        all_target_ids = [org_id] + basements + videos
        placeholders = ', '.join(['?'] * len(all_target_ids))
        cur.execute(f"DELETE FROM api_keys WHERE target_id IN ({placeholders})", all_target_ids)
        
        # Finally, delete the organization
        cur.execute("DELETE FROM organizations WHERE UPPER(TRIM(org_id)) = UPPER(TRIM(?))", (org_id,))
        
        conn.commit()
        return {"status": "success", "message": f"Organization {org_id} and all its data deleted."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@router.get("/organization-details/{org_id}")
def get_org_full_details(org_id: str):
    """Returns a nested structure of basements, cameras, and keys for an org."""
    conn = db()
    cur = conn.cursor()
    
    # 1. Org Info
    cur.execute("SELECT * FROM organizations WHERE org_id=?", (org_id,))
    org = dict(cur.fetchone())
    
    # 2. Basements
    cur.execute("SELECT * FROM basements WHERE org_id=?", (org_id,))
    basements = [dict(r) for r in cur.fetchall()]
    
    # 3. Videos
    for b in basements:
        cur.execute("SELECT * FROM videos WHERE basement_id=?", (b["basement_id"],))
        b["videos"] = [dict(r) for r in cur.fetchall()]
        
    # 4. API Keys (Search by target_id being one of the entities)
    all_targets = [org_id] + [b["basement_id"] for b in basements]
    for b in basements:
        all_targets.extend([v["video_id"] for v in b.get("videos", [])])
    
    if all_targets:
        placeholders = ', '.join(['?'] * len(all_targets))
        cur.execute(f"SELECT * FROM api_keys WHERE target_id IN ({placeholders})", all_targets)
        keys = [dict(r) for r in cur.fetchall()]
    else:
        keys = []
    
    conn.close()
    
    return {
        "organization": org,
        "basements": basements,
        "api_keys": keys
    }

@router.get("/all-basements")
def list_all_basements():
    """Returns every basement in the system with org info."""
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT b.*, o.name as org_name
        FROM basements b
        JOIN organizations o ON b.org_id = o.org_id
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.get("/all-cameras")
def list_all_cameras():
    """Returns every camera in the system with health and org info."""
    conn = db()
    cur = conn.cursor()
    # Use LEFT JOIN to catch cameras with broken basement links
    cur.execute("""
        SELECT v.video_id, v.last_heartbeat, v.is_active, 
               COALESCE(b.name, 'UNKNOWN BASEMENT') as basement_name, 
               COALESCE(o.name, 'SYSTEM/ORPHAN') as org_name
        FROM videos v
        LEFT JOIN basements b ON v.basement_id = b.basement_id
        LEFT JOIN organizations o ON b.org_id = o.org_id
    """)
    rows = cur.fetchall()
    conn.close()
    
    now = time.time()
    cameras = []
    for r in rows:
        d = dict(r)
        # 15 second threshold for Online status
        d["status"] = "Online" if (now - d.get("last_heartbeat", 0)) < 15 else "Offline"
        cameras.append(d)
    return cameras

@router.post("/toggle-video/{video_id}")
def toggle_video(video_id: str, active: int):
    """Enables or disables a specific camera feed. Purges data if disabling."""
    conn = db()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE videos SET is_active = ? WHERE video_id = ?", (active, video_id))
        if not active:
            # Instant purge of slot data when stopped
            cur.execute("DELETE FROM slots WHERE video_id = ?", (video_id,))
        
        conn.commit()
        status = "enabled" if active else "disabled"
        return {"status": "success", "message": f"Camera {video_id} is now {status}."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@router.delete("/delete-video/{video_id}")
def delete_video(video_id: str):
    """Deletes a specific camera and its associated slots and API keys."""
    conn = db()
    cur = conn.cursor()
    try:
        # 1. Delete slots
        cur.execute("DELETE FROM slots WHERE video_id = ?", (video_id,))
        # 2. Delete linked device keys
        cur.execute("DELETE FROM api_keys WHERE key_type='device' AND target_id = ?", (video_id,))
        # 3. Delete the video itself
        cur.execute("DELETE FROM videos WHERE video_id = ?", (video_id,))
        
        conn.commit()
        return {"status": "success", "message": f"Camera {video_id} and its data deleted."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@router.get("/logs")
def get_logs():
    """Returns the most recent 100 system logs with org names."""
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT l.*, o.name as org_name
        FROM system_logs l
        LEFT JOIN organizations o ON l.org_id = o.org_id
        ORDER BY l.id DESC LIMIT 100
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/add-log")
def add_log(level: str, source: str, message: str, org_id: str = None):
    """Internal endpoint to record system events or errors with client context."""
    conn = db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO system_logs (timestamp, org_id, level, source, message)
            VALUES (?, ?, ?, ?, ?)
        """, (time.time(), org_id, level, source, message))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
