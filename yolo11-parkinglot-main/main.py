import cv2
from ultralytics import solutions

video_path = "parking1.mp4"          # your video
json_file = "bounding_boxes.json"    # your polygons

cap = cv2.VideoCapture(video_path)
assert cap.isOpened(), "Error opening video"

w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter("parking_output_with_counts.mp4", fourcc, fps, (w, h))

parking_manager = solutions.ParkingManagement(
    model="yolo11s.pt",
    json_file=json_file,
    classes=[2],      # car class
    conf=0.25,
    iou=0.7,
    show=False        # we control the window ourselves
)

frame_idx = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    result = parking_manager(frame)
    im0 = result.plot_im  # frame with polygons + boxes

    # ---- get occupancy info from Ultralytics ----
    info = parking_manager.pr_info or {}
    occupied = info.get("occupied", 0)
    available = info.get("available", 0)
    total = info.get("total_slots", occupied + available)

    text = f"Frame {frame_idx} | Total: {total}  Occupied: {occupied}  Free: {available}"
    cv2.rectangle(im0, (10, 10), (520, 40), (0, 0, 0), -1)
    cv2.putText(im0, text, (15, 33),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (255, 255, 255), 2, cv2.LINE_AA)

    out.write(im0)
    cv2.imshow("Parking (SPACE/any key = next, ESC = quit)", im0)

    # ---- frame-by-frame: wait for key each frame ----
    key = cv2.waitKey(0) & 0xFF   # 0 = wait indefinitely
    if key == 27:  # ESC
        break

    frame_idx += 1

cap.release()
out.release()
cv2.destroyAllWindows()
