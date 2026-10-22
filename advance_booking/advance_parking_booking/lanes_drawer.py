import cv2
import json
import math
import numpy as np

IMAGE_PATH = "output.jpg"
SAVE_JSON = "data/video.json"

nodes = {}
edges = []
current_lane = []
node_id = 0
entry_point = None

# ---------- VIEW ----------
zoom = 1.0
pan_x, pan_y = 0, 0
dragging = False
mouse_x, mouse_y = 0, 0
lx, ly = 0, 0

# ---------- HELPERS ----------
def dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def nearest_node(pt, th=12):
    for k, v in nodes.items():
        if dist(v, pt) < th:
            return k
    return None

def screen_to_world(x, y):
    return int((x-pan_x)/zoom), int((y-pan_y)/zoom)

def world_to_screen(x, y):
    return int(x*zoom+pan_x), int(y*zoom+pan_y)

# ---------- MOUSE ----------
def mouse(event, x, y, flags, param):
    global node_id, current_lane, dragging
    global zoom, pan_x, pan_y, lx, ly, mouse_x, mouse_y

    mouse_x, mouse_y = x, y
    wx, wy = screen_to_world(x, y)

    if event == cv2.EVENT_LBUTTONDOWN:
        nid = nearest_node((wx, wy))
        if nid is None:
            nid = f"N{node_id}"
            nodes[nid] = (wx, wy)
            node_id += 1
        if current_lane:
            edges.append([current_lane[-1], nid])
        current_lane.append(nid)

    elif event == cv2.EVENT_RBUTTONDOWN:
        current_lane = []

    elif event == cv2.EVENT_MBUTTONDOWN:
        dragging = True
        lx, ly = x, y

    elif event == cv2.EVENT_MOUSEMOVE and dragging:
        pan_x += x-lx
        pan_y += y-ly
        lx, ly = x, y

    elif event == cv2.EVENT_MBUTTONUP:
        dragging = False

    elif event == cv2.EVENT_MOUSEWHEEL:
        zoom *= 1.2 if flags > 0 else 0.8
        zoom = max(0.5, min(zoom, 6))

# ---------- UI ----------
img = cv2.imread(IMAGE_PATH)
if img is None:
    raise FileNotFoundError(f"Image not found: {IMAGE_PATH}")

cv2.namedWindow("LANE DRAWER")
cv2.setMouseCallback("LANE DRAWER", mouse)

print("""
CONTROLS
--------------------------------
Left Click      : Add lane node
Right Click     : Finish current lane
Mouse Wheel     : Zoom
Middle Drag     : Pan
Z               : Undo last point
U               : Undo last edge
E               : Set ENTRY at mouse
ESC             : Save & Exit
--------------------------------
""")

while True:
    canvas = img.copy()

    for a, b in edges:
        cv2.line(
            canvas,
            world_to_screen(*nodes[a]),
            world_to_screen(*nodes[b]),
            (255, 200, 0), 2
        )

    for p in nodes.values():
        cv2.circle(canvas, world_to_screen(*p), 4, (0, 0, 255), -1)

    if entry_point:
        cv2.circle(canvas, world_to_screen(*entry_point), 8, (0,255,0), -1)
        cv2.putText(canvas, "ENTRY",
                    world_to_screen(*entry_point),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0,255,0), 2)

    cv2.imshow("LANE DRAWER", canvas)
    k = cv2.waitKey(1) & 0xFF

    if k == 27:
        break
    elif k == ord('z') and current_lane:
        current_lane.pop()
    elif k == ord('u') and edges:
        edges.pop()
    elif k == ord('e'):
        entry_point = screen_to_world(mouse_x, mouse_y)
        print("✅ ENTRY SET:", entry_point)

cv2.destroyAllWindows()

with open(SAVE_JSON, "w") as f:
    json.dump({
        "entry": entry_point,
        "nodes": nodes,
        "edges": edges
    }, f, indent=2)

print("✅ lanes.json saved with ENTRY")
