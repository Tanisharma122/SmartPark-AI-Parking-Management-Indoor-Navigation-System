import json
from pathlib import Path

import cv2
import numpy as np


# ================== CONFIG ==================

# Canvas size (match this to your camera frame size)
WIDTH, HEIGHT = 1920, 1080

# Colors (BGR)
COLOR_BG = (10, 10, 10)       # near-black background
COLOR_SLOT_FREE = (0, 180, 0) # green
COLOR_SLOT_OCC = (0, 0, 220)  # red
COLOR_SLOT_BORDER = (80, 80, 80)
COLOR_LANE = (200, 200, 0)    # yellow
COLOR_TEXT = (230, 230, 230)
COLOR_PANEL_BG = (25, 25, 25)
COLOR_PANEL_ACCENT = (0, 180, 0)

FONT = cv2.FONT_HERSHEY_SIMPLEX

OUTPUT_PATH = "hikvision_style_map.png"
STATUS_JSON = "slot_status.json"


# ================== SLOT & MAP LAYOUT ==================
# You can design any layout here; this is just an example row+column pattern.

def build_slot_layout():
    """
    Returns a list of slot dicts with positions/sizes.
    All coordinates are in the same 1920x1080 space.
    """
    slots = []

    # Example: three long rows in the center area
    start_x = 400
    start_y = 200
    slot_w = 70
    slot_h = 140
    gap_x = 15
    gap_y = 40

    # Row 1 (top)
    for i in range(10):
        x = start_x + i * (slot_w + gap_x)
        y = start_y
        slots.append({"id": f"S{i+1}", "x": x, "y": y, "w": slot_w, "h": slot_h})

    # Row 2 (middle)
    base_idx = len(slots)
    for i in range(10):
        x = start_x + i * (slot_w + gap_x)
        y = start_y + slot_h + gap_y
        slots.append({"id": f"S{base_idx + i + 1}", "x": x, "y": y, "w": slot_w, "h": slot_h})

    # Row 3 (bottom)
    base_idx = len(slots)
    for i in range(10):
        x = start_x + i * (slot_w + gap_x)
        y = start_y + 2 * (slot_h + gap_y)
        slots.append({"id": f"S{base_idx + i + 1}", "x": x, "y": y, "w": slot_w, "h": slot_h})

    return slots


def build_lane_elements():
    """
    Lanes / arrows / extra decorations.
    Returns simple lists of lines and arrows to draw.
    """
    lanes = []
    arrows = []

    # Vertical lane left side
    lanes.append(((350, 150), (350, 780)))
    lanes.append(((350, 780), (350, 900)))

    # Horizontal lane at bottom
    lanes.append(((350, 900), (1700, 900)))

    # Couple of arrows for direction
    arrows.append(((360, 880), (600, 880)))  # right arrow
    arrows.append(((340, 700), (340, 450)))  # up arrow

    return lanes, arrows


# ================== UTILITIES ==================

def load_status():
    """
    Reads STATUS_JSON and returns dict: slot_id -> status.
    """
    path = Path(STATUS_JSON)
    if not path.exists():
        print(f"[WARN] {STATUS_JSON} not found, treating all as free.")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    status_map = {}
    for item in data:
        sid = str(item.get("id"))
        st = str(item.get("status", "free")).lower()
        if st not in {"free", "occupied"}:
            st = "free"
        status_map[sid] = st
    return status_map


def draw_panel(img, slots, status_map):
    """
    Draws the right stats panel similar to Hikvision: total, occupied, free.
    """
    x0 = WIDTH - 360
    y0 = 40
    x1 = WIDTH - 40
    y1 = HEIGHT - 40

    # Panel background
    cv2.rectangle(img, (x0, y0), (x1, y1), COLOR_PANEL_BG, thickness=-1)
    cv2.rectangle(img, (x0, y0), (x1, y1), (60, 60, 60), thickness=1)

    total = len(slots)
    occ = sum(1 for s in slots if status_map.get(s["id"], "free") == "occupied")
    free = total - occ

    # Title
    cv2.putText(img, "Occupancy", (x0 + 20, y0 + 35),
                FONT, 0.9, COLOR_TEXT, 2, cv2.LINE_AA)

    # Total
    cv2.putText(img, f"Total: {total}", (x0 + 20, y0 + 80),
                FONT, 0.7, (180, 180, 180), 2, cv2.LINE_AA)

    # Free (green)
    cv2.putText(img, f"Free: {free}", (x0 + 20, y0 + 130),
                FONT, 0.7, COLOR_SLOT_FREE, 2, cv2.LINE_AA)

    # Occupied (red)
    cv2.putText(img, f"Occupied: {occ}", (x0 + 20, y0 + 180),
                FONT, 0.7, COLOR_SLOT_OCC, 2, cv2.LINE_AA)

    # Legend dots
    cv2.circle(img, (x0 + 25, y0 + 235), 8, COLOR_SLOT_FREE, -1)
    cv2.putText(img, "Free slot", (x0 + 45, y0 + 242),
                FONT, 0.55, (200, 200, 200), 1, cv2.LINE_AA)

    cv2.circle(img, (x0 + 25, y0 + 270), 8, COLOR_SLOT_OCC, -1)
    cv2.putText(img, "Occupied slot", (x0 + 45, y0 + 277),
                FONT, 0.55, (200, 200, 200), 1, cv2.LINE_AA)


def draw_lanes(img, lanes, arrows):
    """
    Draws yellow lanes and arrows.
    """
    # Lanes (thick yellow lines)
    for p1, p2 in lanes:
        cv2.line(img, p1, p2, COLOR_LANE, thickness=6, lineType=cv2.LINE_AA)

    # Arrows
    for p1, p2 in arrows:
        cv2.arrowedLine(img, p1, p2, COLOR_LANE, thickness=4, tipLength=0.03)


def draw_slots(img, slots, status_map):
    """
    Draws parking slots with green/red fill and neat borders.
    """
    for s in slots:
        x, y, w, h = s["x"], s["y"], s["w"], s["h"]
        sid = s["id"]
        status = status_map.get(sid, "free")

        # Choose color by status
        fill_color = COLOR_SLOT_FREE if status == "free" else COLOR_SLOT_OCC

        # Slight rounded effect using overlay for smooth look
        overlay = img.copy()
        pt1 = (x, y)
        pt2 = (x + w, y + h)

        cv2.rectangle(overlay, pt1, pt2, fill_color, thickness=-1)

        alpha = 0.85
        img[:] = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

        # Border
        cv2.rectangle(img, pt1, pt2, COLOR_SLOT_BORDER, thickness=2)

        # Slot ID text (center)
        cx = x + w // 2
        cy = y + h // 2
        cv2.putText(img, sid, (cx - 15, cy + 5),
                    FONT, 0.5, (0, 0, 0), 2, cv2.LINE_AA)


def draw_header(img):
    """
    Draws top bar with title, mimicking Hikvision style.
    """
    bar_h = 60
    cv2.rectangle(img, (0, 0), (WIDTH, bar_h), (20, 20, 20), thickness=-1)

    cv2.putText(img, "Smart Parking Lot 1",
                (40, 40), FONT, 0.9, (230, 230, 230), 2, cv2.LINE_AA)

    # Small red accent bar under title
    cv2.line(img, (40, bar_h - 5), (320, bar_h - 5),
             (0, 0, 180), thickness=3, lineType=cv2.LINE_AA)


# ================== MAIN RENDER ==================

def main():
    # Background
    img = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    img[:] = COLOR_BG

    # Layouts
    slots = build_slot_layout()
    lanes, arrows = build_lane_elements()

    # Load status (from YOLO or sample JSON)
    status_map = load_status()

    # Draw in logical order
    draw_header(img)
    draw_lanes(img, lanes, arrows)
    draw_slots(img, slots, status_map)
    draw_panel(img, slots, status_map)

    # Save and preview
    cv2.imwrite(OUTPUT_PATH, img)
    print(f"Saved: {OUTPUT_PATH}")

    cv2.imshow("Hikvision-style Parking Map", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
