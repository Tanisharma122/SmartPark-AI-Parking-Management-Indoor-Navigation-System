import cv2
from ultralytics import solutions

video_path = "parking1.mp4"
json_file = "bounding_boxes.json"

cap = cv2.VideoCapture(video_path)
assert cap.isOpened(), "Error opening video"

parking_manager = solutions.ParkingManagement(
    model="yolo11s.pt",
    json_file=json_file,
    classes=[2],
    conf=0.25,
    iou=0.7,
    show=False  # we handle imshow ourselves
)

frame_idx = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    result = parking_manager(frame)
    im0 = result.plot_im

    # get counts
    info = parking_manager.pr_info or {}
    occ = info.get("occupied", 0)
    free = info.get("available", 0)
    total = info.get("total_slots", occ + free)

    txt = f"Frame {frame_idx} | Total: {total}  Occ: {occ}  Free: {free}"
    cv2.rectangle(im0, (10, 10), (540, 40), (0, 0, 0), -1)
    cv2.putText(im0, txt, (15, 33),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (255, 255, 255), 2, cv2.LINE_AA)

    cv2.imshow("Parking (any key=next, ESC=quit)", im0)

    key = cv2.waitKey(0) & 0xFF   # wait for key each frame
    if key == 27:  # ESC
        break

    frame_idx += 1

cap.release()
cv2.destroyAllWindows()
