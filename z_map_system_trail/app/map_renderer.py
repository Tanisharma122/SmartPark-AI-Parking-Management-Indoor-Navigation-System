# app/map_renderer.py
import json
from pathlib import Path

import cv2
import numpy as np

from common import IMAGE_WIDTH, IMAGE_HEIGHT, MAP_OUT_PATH, STATUS_JSON_PATH, SLOTS_JSON_PATH


# Colors (BGR)
COLOR_BG = (10, 10, 10)
COLOR_SLOT_FREE = (0, 180, 0)
COLOR_SLOT_OCC = (0, 0, 220)
COLOR_SLOT_BORDER = (80, 80, 80)
COLOR_LANE = (200, 200, 0)
COLOR_TEXT = (230, 230, 230)
COLOR_PANEL_BG = (25, 25, 25)

FONT = cv2.FONT_HERSHEY_SIMPLEX



def load_slots_for_map():
    """
    Load real slot polygons from slots_cam1.json.
    """
    data = json.loads(Path(SLOTS_JSON_PATH).read_text(encoding="utf-8"))
    slots = []
    for idx, s in enumerate(data, start=1):
        pts = np.array(s["points"], dtype=np.int32)
        sid = s.get("id", f"S{idx}")
        slots.append({"id": sid, "points": pts})
    return slots


def build_lanes():
    """
    Optional yellow lanes just for nice CAD look.
    You can tweak these coordinates to match your lot.
    """
    lanes = [
        ((380, 160), (380, 840)),
        ((380, 840), (1750, 840)),
    ]
    arrows = [
        ((390, 820), (650, 820)),  # right
        ((370, 720), (370, 460)),  # up
    ]
    return lanes, arrows


def load_status():
    """
    Read status_cam1.json written by detect_slots.py.
    Returns dict: slot_id -> 'free' / 'occupied'
    """
    path = Path(STATUS_JSON_PATH)
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(d["id"]): d["status"].lower() for d in data}


def draw_panel(img, slots, status_map):
    x0 = IMAGE_WIDTH - 360
    y0 = 40
    x1 = IMAGE_WIDTH - 40
    y1 = IMAGE_HEIGHT - 40

    cv2.rectangle(img, (x0, y0), (x1, y1), COLOR_PANEL_BG, -1)
    cv2.rectangle(img, (x0, y0), (x1, y1), (60, 60, 60), 1)

    total = len(slots)
    occ = sum(1 for s in slots if status_map.get(s["id"], "free") == "occupied")
    free = total - occ

    cv2.putText(img, "Occupancy", (x0 + 20, y0 + 35), FONT, 0.9, COLOR_TEXT, 2)
    cv2.putText(img, f"Total: {total}", (x0 + 20, y0 + 80), FONT, 0.7, (180, 180, 180), 2)
    cv2.putText(img, f"Free: {free}", (x0 + 20, y0 + 130), FONT, 0.7, COLOR_SLOT_FREE, 2)
    cv2.putText(img, f"Occupied: {occ}", (x0 + 20, y0 + 180), FONT, 0.7, COLOR_SLOT_OCC, 2)


def draw_lanes(img, lanes, arrows):
    for p1, p2 in lanes:
        cv2.line(img, p1, p2, COLOR_LANE, 6, cv2.LINE_AA)
    for p1, p2 in arrows:
        cv2.arrowedLine(img, p1, p2, COLOR_LANE, 4, cv2.LINE_AA, tipLength=0.03)


def draw_slots(img, slots, status_map):
    """
    Draw slots using real polygons from JSON, colored by status.
    """
    for s in slots:
        pts = s["points"]
        sid = s["id"]
        status = status_map.get(sid, "free")

        fill_color = COLOR_SLOT_FREE if status == "free" else COLOR_SLOT_OCC

        overlay = img.copy()
        cv2.fillPoly(overlay, [pts], fill_color)
        img[:] = cv2.addWeighted(overlay, 0.9, img, 0.1, 0)

        cv2.polylines(img, [pts], True, COLOR_SLOT_BORDER, 2)

        cx = int(np.mean(pts[:, 0]))
        cy = int(np.mean(pts[:, 1]))
        cv2.putText(img, sid, (cx - 15, cy + 5),
                    FONT, 0.5, (0, 0, 0), 2, cv2.LINE_AA)



def draw_header(img):
    bar_h = 60
    cv2.rectangle(img, (0, 0), (IMAGE_WIDTH, bar_h), (20, 20, 20), -1)
    cv2.putText(img, "Smart Parking Lot 1", (40, 40), FONT, 0.9, (230, 230, 230), 2)
    cv2.line(img, (40, bar_h - 5), (320, bar_h - 5), (0, 0, 180), 3, cv2.LINE_AA)


def render_map():
    img = np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH, 3), np.uint8)
    img[:] = COLOR_BG

    # OLD:
    # slots = build_slot_layout()

    # NEW:
    slots = load_slots_for_map()
    lanes, arrows = build_lanes()
    status_map = load_status()

    draw_header(img)
    draw_lanes(img, lanes, arrows)
    draw_slots(img, slots, status_map)
    draw_panel(img, slots, status_map)

    cv2.imwrite(MAP_OUT_PATH, img)
    return img
