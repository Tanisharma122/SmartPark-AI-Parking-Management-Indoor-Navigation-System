# from fastapi import Header, Query, HTTPException, Request
# from database import db
# from typing import Optional

# def verify_api_key(
#     request: Request,
#     x_api_key: Optional[str] = Header(None),
#     api_key: Optional[str] = Query(None)
# ):
#     # 1. Look for key in Header OR Query Parameter
#     # This allows it to work in Python (Header) AND Browser (Query Param)
#     token = x_api_key or api_key

#     # 2. If it is a Dashboard or Navigation route, we can be more flexible
#     # BUT for Camera updates, we MUST have a key.
#     is_camera_route = "/update-slots" in request.url.path

#     if not token:
#         if is_camera_route:
#             raise HTTPException(status_code=403, detail="X-API-KEY header is required for camera updates.")
#         else:
#             # For dashboard/navigation, give a friendly hint if they just click the link
#             raise HTTPException(
#                 status_code=403, 
#                 detail="Access Denied. Please add ?api_key=sp_live_3fa85f64a12b9d9a8e5f3c2b1a0d4e6f to your link or visit /docs"
#             )

#     # 3. Validate against DB
#     conn = db()
#     cur = conn.cursor()
#     cur.execute("SELECT 1 FROM api_keys WHERE key=? AND active=1", (token,))
#     valid = cur.fetchone()
#     conn.close()

#     if not valid:
#         raise HTTPException(status_code=401, detail="Invalid API Key provided.")

#     return token

from fastapi import Header, Query, HTTPException, Request
from database import db
from typing import Optional


def verify_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    api_key: Optional[str] = Query(None)
):
    """
    SaaS Auth Logic:
    - DEVICE key → used by cameras (videos)
    - ORG key → used by dashboard/admin
    """

    # 1️⃣ Read API key from Header OR Query
    token = x_api_key or api_key

    is_camera_route = "/update-slots" in request.url.path

    if not token:
        raise HTTPException(
            status_code=403,
            detail="API key is required. If using a browser, append ?api_key=YOUR_KEY to the URL (e.g., ?api_key=sk_org_dashboard_123)"
        )

    # 2️⃣ Validate key from DB
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT key_type, target_id
        FROM api_keys
        WHERE key=? AND is_active=1
    """, (token,))

    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid API Key.")

    key_type = row["key_type"]
    target_id = row["target_id"]
    
    org_id = None
    basement_id = None
    video_id = None

    # Resolve context based on key_type
    if key_type == "org":
        org_id = target_id
    elif key_type == "basement":
        basement_id = target_id
        cur.execute("SELECT org_id FROM basements WHERE basement_id=?", (basement_id,))
        b_row = cur.fetchone()
        if b_row:
            org_id = b_row["org_id"]
    elif key_type == "device":
        video_id = target_id
        cur.execute("SELECT basement_id FROM videos WHERE video_id=?", (video_id,))
        v_row = cur.fetchone()
        if v_row:
            basement_id = v_row["basement_id"]
            cur.execute("SELECT org_id FROM basements WHERE basement_id=?", (basement_id,))
            b_row = cur.fetchone()
            if b_row:
                org_id = b_row["org_id"]

    conn.close()

    is_ingestion = "/update-slots" in request.url.path
    is_navigation = "/navigation-data/" in request.url.path or "/get-path/" in request.url.path or "/video-free-slots/" in request.url.path

    # 3️⃣ DEVICE KEY LOGIC
    if key_type == "device":
        # Can always ingest
        if is_ingestion:
            request.state.org_id = org_id
            request.state.basement_id = basement_id
            request.state.video_id = video_id
            request.state.key_type = "device"
            return token
            
        # Can access its OWN navigation data
        if is_navigation:
            # For navigation-data/{video_id} or get-path/{video_id}/{slot_id}
            path_parts = request.url.path.strip("/").split("/")
            requested_vid = None
            
            if "navigation-data" in path_parts:
                requested_vid = path_parts[path_parts.index("navigation-data") + 1]
            elif "get-path" in path_parts:
                requested_vid = path_parts[path_parts.index("get-path") + 1]
            elif "video-free-slots" in path_parts:
                requested_vid = path_parts[path_parts.index("video-free-slots") + 1]

            if requested_vid and requested_vid != video_id:
                raise HTTPException(status_code=403, detail=f"Device key limited to video {video_id}.")
            
            request.state.org_id = org_id
            request.state.video_id = video_id
            request.state.key_type = "device"
            return token

        raise HTTPException(status_code=403, detail="Device keys can only update slots or view their own navigation.")

    # 4️⃣ ORG KEY LOGIC
    if key_type == "org":
        request.state.org_id = org_id
        request.state.key_type = "org"
        return token

    # 5️⃣ BASEMENT KEY LOGIC (Optional, if needed)
    if key_type == "basement":
        request.state.org_id = org_id
        request.state.basement_id = basement_id
        request.state.key_type = "basement"
        return token

    raise HTTPException(status_code=401, detail="Invalid key type.")
