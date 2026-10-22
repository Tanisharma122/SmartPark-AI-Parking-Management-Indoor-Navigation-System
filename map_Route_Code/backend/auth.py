from fastapi import Header, Query, HTTPException, Request
from database import db
from typing import Optional

def verify_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None),
    api_key: Optional[str] = Query(None)
):
    # 1. Look for key in Header OR Query Parameter
    # This allows it to work in Python (Header) AND Browser (Query Param)
    token = x_api_key or api_key

    # 2. If it is a Dashboard or Navigation route, we can be more flexible
    # BUT for Camera updates, we MUST have a key.
    is_camera_route = "/update-slots" in request.url.path

    if not token:
        if is_camera_route:
            raise HTTPException(status_code=403, detail="X-API-KEY header is required for camera updates.")
        else:
            # For dashboard/navigation, give a friendly hint if they just click the link
            raise HTTPException(
                status_code=403, 
                detail="Access Denied. Please add ?api_key=sp_live_3fa85f64a12b9d9a8e5f3c2b1a0d4e6f to your link or visit /docs"
            )

    # 3. Validate against DB
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM api_keys WHERE key=? AND active=1", (token,))
    valid = cur.fetchone()
    conn.close()

    if not valid:
        raise HTTPException(status_code=401, detail="Invalid API Key provided.")

    return token
