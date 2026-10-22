import cv2
from ultralytics import solutions
import json
import numpy as np
import heapq
import math

# ---------- CONFIG ----------
IMAGE_PATH = "2.jpg"                # image you labeled
SLOTS_JSON = "bounding_boxes2.json"  # list of {"points": [...]}
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

# ---------- DEFINE GRAPH (EDIT THIS FOR YOUR LOT) ----------
# Use image coordinates (same as slot polygons).
# Example: entrance at bottom-center, nodes in front of each slot row.
# Replace these with real coordinates you read from your image in e.g. Paint or OpenCV.

nodes = {
    "E":  (1000, 2000),   # entrance point (example)
    "N1": (600,  1000),   # lane points near slots
    "N2": (1200, 1000),
    "N3": (1800, 1000),
    # ... add more as needed
}

# edges: node -> list of (neighbor, distance)
def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

edges = {
    "E":  [("N1", dist(nodes["E"], nodes["N1"]))],
    "N1": [("E",  dist(nodes["E"], nodes["N1"])),
           ("N2", dist(nodes["N1"], nodes["N2"]))],
    "N2": [("N1", dist(nodes["N1"], nodes["N2"])),
           ("N3", dist(nodes["N2"], nodes["N3"]))],
    "N3": [("N2", dist(nodes["N2"], nodes["N3"]))],
    # ... add rest of lane connectivity
}

# map each slot ID -> nearest node on lane
slot_node = {
    "S1": "N1",
    "S2": "N1",
    "S3": "N2",
    "S4": "N2",
    "S5": "N3",
    # ... continue mapping for all slots
}

entry_node = "E"

# ---------- UTILS ----------
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


def dijkstra(graph, start):
    dist = {node: math.inf for node in graph}
    prev = {node: None for node in graph}
    dist[start] = 0.0
    pq = [(0.0, start)]

    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, w in graph[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    return dist, prev


def reconstruct_path(prev, start, goal):
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        if cur == start:
            break
        cur = prev[cur]
    path.reverse()
    return path


# ---------- INIT PARKING MANAGEMENT ----------
pm = solutions.ParkingManagement(
    model=MODEL_PATH,
    json_file=SLOTS_JSON,
    conf=CONF_THRES,
    iou=IOU_THRES,
    show=False,
    show_in=False,
    show_out=False
)

print("✅ Smart Parking (Image) Started")

# ---------- LOAD IMAGE ----------
img = cv2.imread(IMAGE_PATH)
assert img is not None, f"Error loading: {IMAGE_PATH}"
h, w = img.shape[:2]

# ---------- RUN YOLO + SLOT STATUS ----------
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

# ---------- FIND NEAREST FREE SLOT ----------
best_slot = None
best_dist = math.inf
route_points = []

if free_ids:
    # compute shortest paths from entrance to all nodes
    dist_all, prev_all = dijkstra(edges, entry_node)

    for sid in free_ids:
        if sid not in slot_node:
            continue
        node = slot_node[sid]
        d = dist_all.get(node, math.inf)
        if d < best_dist:
            best_dist = d
            best_slot = sid

    if best_slot is not None:
        dest_node = slot_node[best_slot]
        node_path = reconstruct_path(prev_all, entry_node, dest_node)
        route_points = [nodes[n] for n in node_path]
        print("Nearest free slot:", best_slot)
        print("Path nodes:", node_path)
else:
    print("No free slots.")


# ---------- VISUALIZE ----------
im0 = img.copy()

# color slots by status
for slot in SLOTS:
    pts = np.array(slot["points"], dtype=np.int32)
    sid = slot["id"]

    color = (0, 255, 0) if slot_status[sid] == "free" else (0, 0, 255)

    overlay = im0.copy()
    cv2.fillPoly(overlay, [pts], color)
    alpha = 0.25
    im0 = cv2.addWeighted(overlay, alpha, im0, 1 - alpha, 0)

    cv2.polylines(im0, [pts], True, color, 2)

    cx = int(np.mean(pts[:, 0]))
    cy = int(np.mean(pts[:, 1]))
    cv2.putText(im0, sid, (cx + 5, cy - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

# ---------- DRAW ROUTE AND NODES ----------
# draw route (yellow line) and mark E / nearest slot node
if route_points:
    # route_points is list of (x,y) from nodes[n]
    for i in range(len(route_points) - 1):
        x1, y1 = map(int, route_points[i])
        x2, y2 = map(int, route_points[i + 1])
        cv2.line(im0, (x1, y1), (x2, y2), (0, 255, 255), 4)  # yellow path

    # draw entrance node E
    ex, ey = map(int, nodes[entry_node])
    cv2.circle(im0, (ex, ey), 7, (255, 255, 0), -1)
    cv2.putText(im0, "E", (ex + 8, ey - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    # draw target lane node for best slot
    target_node = slot_node[best_slot]
    tx, ty = map(int, nodes[target_node])
    cv2.circle(im0, (tx, ty), 7, (0, 255, 255), -1)
    cv2.putText(im0, target_node, (tx + 8, ty - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    # optional: also write the slot id near the lane node
    cv2.putText(im0, f"Slot {best_slot}", (tx + 8, ty + 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)


# right-side overlay
x0 = w - 260
y0 = 40
dy = 24

font = cv2.FONT_HERSHEY_SIMPLEX

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

cv2.imshow("Smart Parking - Image", im0)
cv2.imwrite("output_with_route.jpg", im0)
cv2.waitKey(0)
cv2.destroyAllWindows()
print("✅ Finished (saved to output_with_route.jpg)")
