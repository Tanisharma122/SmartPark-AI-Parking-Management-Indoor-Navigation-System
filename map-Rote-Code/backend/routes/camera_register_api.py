# from fastapi import APIRouter, Request, HTTPException
# from database import db

# router = APIRouter(tags=["Camera Registration"])

# @router.post("/register-camera")
# def register_camera(data: dict, request: Request):
#     basement_id = getattr(request.state, "basement_id", None)
#     if not basement_id:
#         raise HTTPException(status_code=403, detail="Basement context missing")

#     camera_id = data.get("camera_id")
#     cam_type = data.get("type")
#     source = data.get("source")

#     if not camera_id or not cam_type:
#         raise HTTPException(status_code=400, detail="Invalid camera data")

#     conn = db()
#     cur = conn.cursor()

#     cur.execute("""
#         INSERT OR REPLACE INTO cameras
#         (camera_id, basement_id, type, source, is_active)
#         VALUES (?, ?, ?, ?, 1)
#     """, (camera_id, basement_id, cam_type, source))

#     conn.commit()
#     conn.close()

#     return {
#         "message": "Camera registered successfully",
#         "camera_id": camera_id,
#         "basement_id": basement_id
#     }

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Any
import json
from database import db

# Custom Response for Pretty Printing
class PrettyJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=4,
            separators=(", ", ": "),
        ).encode("utf-8")

router = APIRouter(tags=["Video Registration"], default_response_class=PrettyJSONResponse)

@router.post("/register-video")
def register_video(data: dict, request: Request):
    # basement_id comes from DEVICE API key (auth.py)
    basement_id = getattr(request.state, "basement_id", None)
    if not basement_id:
        raise HTTPException(status_code=403, detail="Basement context missing")

    video_id = data.get("video_id") or data.get("camera_id")
    vid_type = data.get("type")
    source = data.get("source")

    if not video_id or not vid_type:
        raise HTTPException(status_code=400, detail="Invalid video data")

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO videos
        (video_id, basement_id, type, source, is_active)
        VALUES (?, ?, ?, ?, 1)
    """, (video_id, basement_id, vid_type, source))

    conn.commit()
    conn.close()

    return {
        "message": "Video registered successfully",
        "video_id": video_id,
        "basement_id": basement_id
    }
