# app/detect_slots.py
import json
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from common import (
    IMAGE_WIDTH,
    IMAGE_HEIGHT,
    MODEL_PATH,
    VIDEO_PATH,
    SLOTS_JSON_PATH,
    STATUS_JSON_PATH,
    FRAME_OUT_PATH,
)
from map_renderer import render_map


# Adapt to your model's class IDs for vehicles
VEHICLE_CLASSES = {0, 1, 2, 3, 5, 7}  # example for COCO (person/car/bus/truck...)
CONF_THR = 0.4


def load_slots():
    """
    Load slot polygons from slots_cam1.json.
    """
    data = json.loads(Path(SLOTS_JSON_PATH).read_text(encoding="utf-8"))
    slots = []
    for idx, s in enumerate(data, start=1):
        pts = np.array(s["points"], dtype=np.int32)
        sid = s.get("id", f"S{idx}")
        slots.append({"id": sid, "points": pts})
    return slots


def point_in_poly(x, y, poly):
    """
    Use OpenCV pointPolygonTest to check if a point is inside a polygon.
    """
    return cv2.pointPolygonTest(poly, (float(x), float(y)), False) >= 0


def compute_status(detections, slots):
    """
    detections: list of (cx, cy) for detected vehicles.
    slots: list with 'id' and 'points'.
    """
    status = {s["id"]: "free" for s in slots}
    for cx, cy in detections:
        for s in slots:
            if point_in_poly(cx, cy, s["points"]):
                status[s["id"]] = "occupied"
    return status


def save_status_json(status):
    data = [{"id": sid, "status": st} for sid, st in status.items()]
    Path(STATUS_JSON_PATH).write_text(json.dumps(data, indent=2), encoding="utf-8")


def draw_frame_overlay(frame, slots, status):
    """
    Draw colored polygons and IDs on the real camera frame.
    """
    for s in slots:
        pts = s["points"]
        sid = s["id"]
        st = status.get(sid, "free")
        color = (0, 255, 0) if st == "free" else (0, 0, 255)

        overlay = frame.copy()
        cv2.fillPoly(overlay, [pts], color)
        frame[:] = cv2.addWeighted(overlay, 0.35, frame, 0.65, 0)

        cv2.polylines(frame, [pts], True, color, 2)
        cx = int(np.mean(pts[:, 0]))
        cy = int(np.mean(pts[:, 1]))
        cv2.putText(
            frame, sid, (cx - 15, cy + 5),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
        )
    return frame


def main():
    model = YOLO(MODEL_PATH)
    slots = load_slots()

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {VIDEO_PATH}")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (IMAGE_WIDTH, IMAGE_HEIGHT))

        # YOLO inference
        result = model.predict(frame, imgsz=IMAGE_WIDTH, conf=CONF_THR, verbose=False)[0]

        # Collect vehicle centers
        car_centers = []
        for box in result.boxes:
            cls_id = int(box.cls)
            if cls_id not in VEHICLE_CLASSES:
                continue
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            car_centers.append((cx, cy))

        # Slot status
        status = compute_status(car_centers, slots)
        save_status_json(status)

        # Draw on real camera frame
        frame_overlay = draw_frame_overlay(frame.copy(), slots, status)
        cv2.imwrite(FRAME_OUT_PATH, frame_overlay)

        # Render CAD map using the same status
        map_img = render_map()

        # Show both in real time
        cv2.imshow("Camera with overlay", frame_overlay)
        cv2.imshow("CAD map", map_img)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
