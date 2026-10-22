# backend/app.py
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional


app = FastAPI(title="Smart Parking Camera API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- API KEYS ----
MASTER_API_KEY = "MASTER-123"
CAMERA_API_KEYS = {
    "cam1": "CAM1-ABC",   # camera 1 key
    "cam2": "CAM2-XYZ",   # camera 2 key
}


class CameraStatus(BaseModel):
    total_slots: int
    free_slots: int
    occupied_slots: int


# ---- CAMERA METADATA ----
CAMERAS: Dict[str, Dict] = {
    "cam1": {
        "name": "Front Gate Camera",
        "lat": 22.564321,
        "lng": 72.934567,
        "floor": "Ground",
        "zone": "A",
        "status": "online",
    },
    "cam2": {
        "name": "Basement Camera",
        "lat": 22.565000,
        "lng": 72.936000,
        "floor": "B1",
        "zone": "B",
        "status": "online",
    },
}

# ---- RUNTIME STATUS (filled by camera nodes) ----
CAMERA_STATUS: Dict[str, CameraStatus] = {
    "cam1": CameraStatus(total_slots=0, free_slots=0, occupied_slots=0),
    "cam2": CameraStatus(total_slots=0, free_slots=0, occupied_slots=0),
}


def check_master(x_api_key: Optional[str]):
    if x_api_key != MASTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


def check_cam(camera_id: str, x_api_key: Optional[str]):
    # master key always allowed
    if x_api_key == MASTER_API_KEY:
        return
    expected = CAMERA_API_KEYS.get(camera_id)
    if expected is None or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid camera API key")


@app.get("/cameras")
def list_cameras(x_api_key: Optional[str] = Header(None)):
    """
    List all cameras with geo + basic info.
    Header: X-API-Key: MASTER-123
    """
    check_master(x_api_key)
    items = []
    for cam_id, data in CAMERAS.items():
        items.append({
            "id": cam_id,
            "name": data["name"],
            "lat": data["lat"],
            "lng": data["lng"],
            "floor": data["floor"],
            "zone": data["zone"],
            "status": data["status"],
        })
    return {"count": len(items), "cameras": items}


@app.get("/cameras/{camera_id}")
def get_camera(camera_id: str, x_api_key: Optional[str] = Header(None)):
    """
    Get single camera info + latest slot counts.
    Header: X-API-Key: MASTER-123 or camera-specific key.
    """
    if camera_id not in CAMERAS:
        raise HTTPException(status_code=404, detail="Camera not found")
    check_cam(camera_id, x_api_key)

    meta = CAMERAS[camera_id]
    status = CAMERA_STATUS.get(camera_id)
    return {
        "id": camera_id,
        "name": meta["name"],
        "lat": meta["lat"],
        "lng": meta["lng"],
        "floor": meta["floor"],
        "zone": meta["zone"],
        "status": meta["status"],
        "total_slots": status.total_slots if status else None,
        "free_slots": status.free_slots if status else None,
        "occupied_slots": status.occupied_slots if status else None,
    }


@app.post("/cameras/{camera_id}/status")
def update_camera_status(
    camera_id: str,
    body: CameraStatus,
    x_api_key: Optional[str] = Header(None),
):
    """
    Called by camera nodes (cam1, cam2) to update counts.
    Header: X-API-Key: that camera's key.
    """
    if camera_id not in CAMERAS:
        raise HTTPException(status_code=404, detail="Camera not found")
    check_cam(camera_id, x_api_key)
    CAMERA_STATUS[camera_id] = body
    return {"ok": True}