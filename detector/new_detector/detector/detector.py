from typing import Dict, List
import cv2
import json
from ultralytics import YOLO
MODEL_PATH = "detector/best.pt"  # adjust path if best.pt is elsewhere
model = YOLO(MODEL_PATH)

def compute_slot_status(image_path: str, slots_config_path: str) -> Dict:
    """
    Run YOLO on a single image and return:
    {
      "total": int,
      "free": ["A1", "A2"],
      "occupied": ["A3", ...]
    }
    """
    # 1) load image
    img = cv2.imread(image_path)

    # 2) load slots polygons
    with open(slots_config_path, "r") as f:
        slots = json.load(f)  # [{"code": "A1", "points": [...]}, ...]

    # 3) run YOLO (pseudo; adapt to your Ultralytics code)
    results = model(img)  # get detections

    # 4) convert detections to slot status (your existing logic)
    free_slots: List[str] = []
    occupied_slots: List[str] = []

    for slot in slots:
        code = slot["code"]
        # TODO: check if any detection overlaps this slot polygon.
        is_occupied = False  # replace with real condition
        if is_occupied:
            occupied_slots.append(code)
        else:
            free_slots.append(code)

    return {
        "total": len(slots),
        "free": free_slots,
        "occupied": occupied_slots
    }


def get_parking_status_for_all_cameras(cameras_cfg) -> Dict:
    """
    Returns:
    {
      "cam1": {"total": ..., "free": [...], "occupied": [...]},
      "cam2": {...}
    }
    """
    status = {}
    for cam in cameras_cfg:
        status[cam["id"]] = compute_slot_status(
            cam["image_path"], cam["slots_config"]
        )
    return status
