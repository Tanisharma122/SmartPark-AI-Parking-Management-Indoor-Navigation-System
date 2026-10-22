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

# ---- CONFIG ----

MASTER_API_KEY = "MASTER-123"
CAMERA_API_KEYS = {
    "cam1": "CAM1-ABC",
    "cam2": "CAM2-XYZ",
}

class CameraStatus(BaseModel):
    total_slots: int
    free_slots: int
    occupied_slots: int

# base metadata
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
        "lat": 22.564900,
        "lng": 72.935100,
        "floor": "B1",
        "zone": "B",
        "status": "offline",
    },
}

# runtime status (to be updated by camera nodes)
CAMERA_STATUS: Dict[str, CameraStatus] = {
    "cam1": CameraStatus(total_slots=20, free_slots=5, occupied_slots=15),
    "cam2": CameraStatus(total_slots=15, free_slots=3, occupied_slots=12),
}


# ---- API KEY HELPERS ----

def check_master_key(x_api_key: Optional[str]):
    if x_api_key != MASTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid master API key")


def check_camera_key(camera_id: str, x_api_key: Optional[str]):
    # master key always allowed
    if x_api_key == MASTER_API_KEY:
        return
    expected = CAMERA_API_KEYS.get(camera_id)
    if expected is None or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid camera API key")


# ---- ENDPOINTS ----

@app.get("/cameras")
def list_cameras(x_api_key: Optional[str] = Header(None)):
    """
    All cameras geo + basic info.
    Use header: X-API-Key: MASTER-123
    """
    check_master_key(x_api_key)
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
    Single camera geo + status.
    Header: X-API-Key: MASTER-123 or that camera's key.
    """
    if camera_id not in CAMERAS:
        raise HTTPException(status_code=404, detail="Camera not found")
    check_camera_key(camera_id, x_api_key)

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
def update_camera_status(camera_id: str, body: CameraStatus,
                         x_api_key: Optional[str] = Header(None)):
    """
    Camera node sends updated slot counts here.
    Header: X-API-Key: that camera's key (CAM1-ABC, CAM2-XYZ)
    """
    if camera_id not in CAMERAS:
        raise HTTPException(status_code=404, detail="Camera not found")
    check_camera_key(camera_id, x_api_key)
    CAMERA_STATUS[camera_id] = body
    return {"ok": True}
