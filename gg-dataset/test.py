from ultralytics import YOLO
import cv2
import json
from pathlib import Path

MODEL_PATH = "best.pt"       # your model
IMAGE_PATH = "2.jpg"      # input image
OUT_IMG    = "2-out.jpg"  # annotated image
OUT_JSON   = "2-out.json" # detection data


def detect_and_save():
    model = YOLO(MODEL_PATH)

    # run inference
    results = model(IMAGE_PATH)
    r = results[0]

    names = model.names

    # draw boxes on image
    im = r.plot()  # numpy array with annotations

    # save annotated image
    cv2.imwrite(OUT_IMG, im)

    # prepare JSON detections
    detections = []
    for box in r.boxes:
        cls_id = int(box.cls[0])
        cls_name = names[cls_id]
        conf = float(box.conf[0])
        x1, y1, x2, y2 = map(float, box.xyxy[0])

        detections.append({
            "class_id": cls_id,
            "class_name": cls_name,
            "confidence": conf,
            "bbox_xyxy": [x1, y1, x2, y2]
        })

    result = {
        "image": str(Path(IMAGE_PATH).name),
        "num_detections": len(detections),
        "detections": detections
    }

    # save JSON
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Saved annotated image to {OUT_IMG}")
    print(f"Saved JSON results to {OUT_JSON}")


if __name__ == "__main__":
    detect_and_save()
