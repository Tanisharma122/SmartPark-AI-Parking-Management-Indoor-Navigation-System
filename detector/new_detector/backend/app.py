from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .cameras_config import CAMERAS
from detector.detector import get_parking_status_for_all_cameras

app = FastAPI()

# allow dashboard frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/free-slots")
def free_slots():
    """
    Return status for all cameras.
    """
    status_all = get_parking_status_for_all_cameras(CAMERAS)
    return status_all


@app.get("/recommendation")
def recommendation():
    """
    Return the FIRST camera (by priority) that still has free slots,
    and its free slot codes. This is where 'if cam1 full then cam2' lives.
    """
    status_all = get_parking_status_for_all_cameras(CAMERAS)

    # sort cameras by priority
    sorted_cams = sorted(CAMERAS, key=lambda c: c["priority"])

    for cam in sorted_cams:
        cid = cam["id"]
        free_slots = status_all[cid]["free"]
        if free_slots:  # at least one free slot
            return {
                "camera": cid,
                "total": status_all[cid]["total"],
                "free_slots": free_slots
            }

    # if none has free slot
    return {
        "camera": None,
        "total": 0,
        "free_slots": []
    }
