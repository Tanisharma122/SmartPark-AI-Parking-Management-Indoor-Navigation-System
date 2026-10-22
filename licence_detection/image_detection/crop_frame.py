from ultralytics import YOLO
import cv2
import os

model = YOLO("yolov8n.pt")
os.makedirs("crops", exist_ok=True)

image_path = "car_licence.png"
results = model(image_path)[0]

img = cv2.imread(image_path)

for i, box in enumerate(results.boxes):
    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
    crop = img[y1:y2, x1:x2]
    cv2.imwrite(f"crops/plate_{i}.jpg", crop)
    print(f"Saved crops/plate_{i}.jpg")
