import cv2
from ultralytics import solutions
import json
import numpy as np

# ---------- CONFIG ----------
IMAGE_PATH = "3.jpg"         # image you labeled
SLOTS_JSON = "bounding_boxes.json"  # list of {"points": [...]}
MODEL_PATH = "best.pt"

CONF_THRES = 0.25
IOU_THRES  = 0.7

# ---------- LOAD SLOTS ----------
with open(SLOTS_JSON, "r", encoding="utf-8") as f:
    regions = json.load(f)  # list of {"points": [...]}

SLOTS = []
for i, region in enumerate(regions, start=1):
    SLOTS.append({
        "id": f"S{i}",
        "points": region["points"]
    })


def box_center(box):
    x1, y1, x2, y2 = box
    return (x1 + x2) / 2.0, (y1 + y2) / 2.0


def point_in_poly(x, y, points):
    pts_array = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
    return cv2.pointPolygonTest(pts_array, (float(x), float(y)), False) >= 0


def get_slot_status(pm_obj):
    """
    For each slot:
      - if ANY detection box center falls inside polygon -> occupied
      - else -> free
    """
    status = {slot["id"]: "free" for slot in SLOTS}
    boxes = pm_obj.boxes

    for box in boxes:
        cx, cy = box_center(box)
        for slot in SLOTS:
            if point_in_poly(cx, cy, slot["points"]):
                status[slot["id"]] = "occupied"

    return status


pm = solutions.ParkingManagement(
    model=MODEL_PATH,
    json_file=SLOTS_JSON,
    conf=CONF_THRES,
    iou=IOU_THRES,
    show=False,
    show_in=False,   # turn off built-in entry counter overlay
    show_out=False   # turn off built-in exit/available overlay
)


print("✅ Smart Parking (Image) Started")

# ---------- LOAD IMAGE (NO RESIZE) ----------
img = cv2.imread(IMAGE_PATH)
assert img is not None, f"Error loading: {IMAGE_PATH}"
h, w = img.shape[:2]

# YOLO + parking
result = pm(img)
slot_status = get_slot_status(pm)

total_slots = len(slot_status)
occ_ids  = [sid for sid, s in slot_status.items() if s == "occupied"]
free_ids = [sid for sid, s in slot_status.items() if s == "free"]
occ_count  = len(occ_ids)
free_count = len(free_ids)

print(f"Total: {total_slots}, Occupied: {occ_count}, Free: {free_count}")
print("Occupied IDs:", occ_ids)
print("Free IDs:", free_ids)

# ---------- VISUALIZE ----------# ---------- VISUALIZE ----------
# im0 = result.plot_im

# ---------- VISUALIZE ----------
im0 = img.copy()   # clean image, no built-in overlays


# color slots by status: green = free, red = occupied
for slot in SLOTS:
    pts = np.array(slot["points"], dtype=np.int32)
    sid = slot["id"]

    color = (0, 255, 0) if slot_status[sid] == "free" else (0, 0, 255)  # green / red

    # optional: semi-transparent fill
    overlay = im0.copy()
    cv2.fillPoly(overlay, [pts], color)
    alpha = 0.25
    im0 = cv2.addWeighted(overlay, alpha, im0, 1 - alpha, 0)

    # outline
    cv2.polylines(im0, [pts], True, color, 2)

    # ID text
    cx = int(np.mean(pts[:, 0]))
    cy = int(np.mean(pts[:, 1]))
    cv2.putText(im0, sid, (cx + 5, cy - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)


# right-side overlay (simpler and less bold)
x0 = w - 260   # closer to right edge
y0 = 40
dy = 24        # tighter spacing

font = cv2.FONT_HERSHEY_SIMPLEX

# semi-transparent small background
overlay_info = im0.copy()
cv2.rectangle(overlay_info, (x0 - 10, y0 - 25), (w - 10, y0 + 4 * dy), (0, 0, 0), -1)
im0 = cv2.addWeighted(overlay_info, 0.4, im0, 0.6, 0)

cv2.putText(im0, f"Slots: {total_slots}", (x0, y0),
            font, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
cv2.putText(im0, f"Occ  : {occ_count}", (x0, y0 + dy),
            font, 0.6, (0, 0, 255), 1, cv2.LINE_AA)
cv2.putText(im0, f"Free : {free_count}", (x0, y0 + 2 * dy),
            font, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

max_show = 6
free_text = ", ".join(free_ids[:max_show]) if free_ids else "None"
cv2.putText(im0, f"Free IDs: {free_text}", (x0, y0 + 3 * dy),
            font, 0.5, (255, 255, 0), 1, cv2.LINE_AA)

#----------------------output 
cv2.imshow("Smart Parking - Image", im0)
cv2.imwrite("3-output.jpg", im0)
cv2.waitKey(0)
cv2.destroyAllWindows()
print("✅ Finished (saved to 3-output.jpg)")
