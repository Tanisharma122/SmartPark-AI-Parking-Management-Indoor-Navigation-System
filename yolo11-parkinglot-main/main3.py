import cv2
from ultralytics import solutions

video_path = "parking1.mp4"
json_file = "bounding_boxes.json"

cap = cv2.VideoCapture(video_path)
assert cap.isOpened(), "Error opening video"

parking_manager = solutions.ParkingManagement(
    model="yolo11s.pt",
    json_file=json_file,
    classes=[2],      # car
    conf=0.25,
    iou=0.7,
    show=True         # let Ultralytics handle window and counts
)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    _ = parking_manager(frame)  # processes and shows frame + counts

    # Ultralytics shows window; ESC closes it
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
