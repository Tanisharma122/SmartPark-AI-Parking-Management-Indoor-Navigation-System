import json
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


# -------- CONFIG --------
MODEL_PATH = "models/best.pt"
VIDEO_PATH = "data/video.mp4"
SLOTS_JSON = "data/slots_cam1.json"

# will resize every frame to this size (must match labeling size)
IMAGE_WIDTH = 1920
IMAGE_HEIGHT = 1080

COLOR_BG = (10, 10, 10)
COLOR_SLOT_FREE = (0, 180, 0)
COLOR_SLOT_OCC = (0, 0, 220)
COLOR_BORDER = (80, 80, 80)
FONT = cv2.FONT_HERSHEY_SIMPLEX

# adapt to your model (vehicle class IDs)
VEHICLE_CLASSES = {0, 1, 2, 3, 5, 7}
CONF_THR = 0.4


# -------- DATA LOADERS --------

def load_slots():
    data = json.loads(Path(SLOTS_JSON).read_text(encoding="utf-8"))
    slots = []
    for idx, s in enumerate(data, start=1):
        pts = np.array(s["points"], dtype=np.int32)
        sid = s.get("id", f"S{idx}")
        slots.append({"id": sid, "points": pts})
    return slots


def point_in_poly(x, y, poly):
    return cv2.pointPolygonTest(poly, (float(x), float(y)), False) >= 0


# -------- STATUS FROM YOLO --------

def compute_status_from_yolo(model, frame, slots):
    """
    Run YOLO on frame, compute free/occupied per slot.
    """
    result = model.predict(frame, imgsz=IMAGE_WIDTH, conf=CONF_THR, verbose=False)[0]

    # collect vehicle centers
    centers = []
    for box in result.boxes:
        cls_id = int(box.cls)
        if cls_id not in VEHICLE_CLASSES:
            continue
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        centers.append((cx, cy))

    status = {s["id"]: "free" for s in slots}
    for cx, cy in centers:
        for s in slots:
            if point_in_poly(cx, cy, s["points"]):
                status[s["id"]] = "occupied"
    return status


# -------- DRAW ON REAL FRAME --------

def draw_on_frame(frame, slots, status):
    for s in slots:
        pts = s["points"]
        sid = s["id"]
        st = status.get(sid, "free")
        color = COLOR_SLOT_FREE if st == "free" else COLOR_SLOT_OCC

        overlay = frame.copy()
        cv2.fillPoly(overlay, [pts], color)
        frame[:] = cv2.addWeighted(overlay, 0.35, frame, 0.65, 0)

        cv2.polylines(frame, [pts], True, color, 2)
        cx = int(np.mean(pts[:, 0]))
        cy = int(np.mean(pts[:, 1]))
        cv2.putText(frame, sid, (cx - 15, cy + 5),
                    FONT, 0.5, color, 2, cv2.LINE_AA)
    return frame


# -------- DRAW CAD MAP FROM STATUS --------

def draw_map(slots, status):
    img = np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH, 3), np.uint8)
    img[:] = COLOR_BG
    for s in slots:
        pts = s["points"]
        sid = s["id"]
        st = status.get(sid, "free")
        fill = COLOR_SLOT_FREE if st == "free" else COLOR_SLOT_OCC
        overlay = img.copy()
        cv2.fillPoly(overlay, [pts], fill)
        img[:] = cv2.addWeighted(overlay, 0.9, img, 0.1, 0)
        cv2.polylines(img, [pts], True, COLOR_BORDER, 2)
        cx = int(np.mean(pts[:, 0])); cy = int(np.mean(pts[:, 1]))
        cv2.putText(img, sid, (cx-15, cy+5),
                    FONT, 0.5, (0,0,0), 2, cv2.LINE_AA)
    return img

# -------- MAIN LOOP --------

def main():
    model = YOLO(MODEL_PATH)
    slots = load_slots()

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {VIDEO_PATH}")

    frame_idx = 0
    status = {s["id"]: "free" for s in slots}  # initial status

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.resize(frame, (IMAGE_WIDTH, IMAGE_HEIGHT))

        # run YOLO only every 5th frame (tune this number: 3, 5, 6, ...)
        if frame_idx % 15 == 0:
            status = compute_status_from_yolo(model, frame, slots)

        frame_vis = draw_on_frame(frame.copy(), slots, status)
        map_img = draw_map(slots, status)

        cv2.imshow("Camera with overlay", frame_vis)
        cv2.imshow("CAD map", map_img)

        # 1 ms wait is fine; main speed gain is from skipping YOLO
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        frame_idx += 1

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
