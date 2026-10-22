import tkinter as tk
from math import hypot
import heapq

# ---------- GEOMETRY / GRAPH HELPERS ----------

def path_length(points):
    total = 0.0
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        total += hypot(x2 - x1, y2 - y1)
    return total

def dijkstra(graph, start):
    dist = {n: float("inf") for n in graph}
    prev = {n: None for n in graph}
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

def dist(a, b):
    return hypot(a[0] - b[0], a[1] - b[1])


# ---------- CONFIG: LAYOUT ----------

# Reference point (entrance)
REF_NODE = "R"

nodes = {
    "R":  (50, 250),    # entrance
    "A":  (100, 250),   # lane bottom left
    "B":  (250, 250),   # lane bottom mid
    "C":  (250, 180),   # lane up near S3/S4
    "D":  (250, 120),   # lane up near S1/S2
}

# build edges on lanes (no slot crossing)
edges = {
    "R": [("A", dist(nodes["R"], nodes["A"]))],
    "A": [("R", dist(nodes["R"], nodes["A"])),
          ("B", dist(nodes["A"], nodes["B"]))],
    "B": [("A", dist(nodes["A"], nodes["B"])),
          ("C", dist(nodes["B"], nodes["C"]))],
    "C": [("B", dist(nodes["B"], nodes["C"])),
          ("D", dist(nodes["C"], nodes["D"]))],
    "D": [("C", dist(nodes["C"], nodes["D"]))],
}

# Slot polygons (rectangles)
SLOTS = {
    "S1": {"poly": [(150, 80), (220, 80), (220, 140), (150, 140)]},
    "S2": {"poly": [(260, 80), (330, 80), (330, 140), (260, 140)]},
    "S3": {"poly": [(150, 190), (220, 190), (220, 250), (150, 250)]},
    "S4": {"poly": [(260, 190), (330, 190), (330, 250), (260, 250)]},
}

# For each slot, define which lane node it attaches to and its attach point on that lane
SLOT_ATTACH = {
    "S1": {"node": "D", "point": (235, 110)},  # small point on lane in front of S1
    "S2": {"node": "D", "point": (265, 110)},
    "S3": {"node": "C", "point": (235, 210)},
    "S4": {"node": "C", "point": (265, 210)},
}

# Add these attach points as separate nodes in graph so the path ends just before the slot
for sid, cfg in SLOT_ATTACH.items():
    attach_name = f"{sid}_ATT"
    ax, ay = cfg["point"]
    lane_node = cfg["node"]
    nodes[attach_name] = (ax, ay)

    # connect attachment to lane node with short edge
    d = dist(nodes[attach_name], nodes[lane_node])
    edges.setdefault(attach_name, []).append((lane_node, d))
    edges.setdefault(lane_node, []).append((attach_name, d))

# Slot status for demo
SLOT_STATUS = {
    "S1": "occupied",
    "S2": "free",
    "S3": "occupied",
    "S4": "free",
}


# ---------- LOGIC ----------

def find_nearest_free_slot():
    # Compute shortest paths from entrance REF_NODE to all nodes
    dist_all, prev_all = dijkstra(edges, REF_NODE)

    best_slot = None
    best_len = float("inf")
    best_attach_node = None
    best_node_path = []
    best_geo_path = []

    for sid, status in SLOT_STATUS.items():
        if status != "free":
            continue

        attach_node = f"{sid}_ATT"
        if attach_node not in nodes:
            continue

        d = dist_all.get(attach_node, float("inf"))
        if d < best_len:
            best_len = d
            best_slot = sid
            best_attach_node = attach_node

    if best_slot is None:
        return None, [], []

    # reconstruct node path and convert to coordinates
    _, prev_all = dijkstra(edges, REF_NODE)  # recompute or reuse
    node_path = reconstruct_path(prev_all, REF_NODE, best_attach_node)
    coord_path = [nodes[n] for n in node_path]

    return best_slot, node_path, coord_path


# ---------- TKINTER UI ----------

root = tk.Tk()
root.title("Parking Path Demo (Lane-based)")

canvas = tk.Canvas(root, width=420, height=320, bg="white")
canvas.pack(padx=10, pady=10)

info_label = tk.Label(root, text="Click 'Compute Path' to highlight shortest lane path.")
info_label.pack(pady=5)


def draw_scene(highlight_slot=None, coord_path=None):
    canvas.delete("all")

    # draw lanes (edges between lane nodes only)
    lane_nodes = ["R", "A", "B", "C", "D"]
    for u in lane_nodes:
        for v, _ in edges.get(u, []):
            if v not in lane_nodes:
                continue
            x1, y1 = nodes[u]
            x2, y2 = nodes[v]
            canvas.create_line(x1, y1, x2, y2, fill="#cccccc", width=3)

    # draw reference node
    rx, ry = nodes[REF_NODE]
    canvas.create_oval(rx - 5, ry - 5, rx + 5, ry + 5, fill="blue")
    canvas.create_text(rx + 15, ry, text="R", anchor="w", fill="blue")

    # draw slots
    for sid, data in SLOTS.items():
        pts = data["poly"]
        coords = []
        for x, y in pts:
            coords.extend((x, y))

        status = SLOT_STATUS.get(sid, "free")
        if status == "free":
            fill_color = "#a8f0a8"
            outline = "green"
        else:
            fill_color = "#f0a8a8"
            outline = "red"

        canvas.create_polygon(*coords, fill=fill_color, outline=outline, width=2)

        cx = sum(x for x, _ in pts) / len(pts)
        cy = sum(y for _, y in pts) / len(pts)
        canvas.create_text(cx, cy, text=sid, fill="black")

        # draw attach point
        attach_cfg = SLOT_ATTACH[sid]
        ax, ay = attach_cfg["point"]
        canvas.create_oval(ax - 3, ay - 3, ax + 3, ay + 3,
                           fill="black", outline="black")

    # draw path along lanes to attach point
    if highlight_slot and coord_path:
        # orange path
        if len(coord_path) >= 2:
            path_coords = []
            for x, y in coord_path:
                path_coords.extend((x, y))
            canvas.create_line(*path_coords, fill="orange", width=4, smooth=True)

        # highlight attach point and slot label
        ax, ay = SLOT_ATTACH[highlight_slot]["point"]
        canvas.create_oval(ax - 4, ay - 4, ax + 4, ay + 4,
                           fill="orange", outline="black")
        canvas.create_text(ax + 10, ay,
                           text=f"{highlight_slot} (target)", anchor="w", fill="orange")


def on_compute_path():
    best_slot, node_path, coord_path = find_nearest_free_slot()
    if best_slot is None:
        info_label.config(text="No free slots.")
        draw_scene(None, None)
    else:
        info_label.config(text=f"Nearest free slot: {best_slot} | Path: {node_path}")
        draw_scene(best_slot, coord_path)


btn = tk.Button(root, text="Compute Path", command=on_compute_path)
btn.pack(pady=5)

draw_scene()

root.mainloop()
