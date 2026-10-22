import cv2
import numpy as np

# Canvas size (tweak if you want)
W, H = 1920, 1080

# Colors (BGR)
COLOR_BG = (0, 0, 0)
COLOR_BORDER = (60, 60, 60)
COLOR_LANE = (0, 255, 255)       # yellow
COLOR_HATCH = (0, 180, 255)      # yellowish for cross hatch
COLOR_SLOT_FREE = (0, 200, 0)    # green
COLOR_SLOT_OCC = (0, 0, 220)     # red
COLOR_TEXT = (0, 255, 0)         # green text
FONT = cv2.FONT_HERSHEY_SIMPLEX


def draw_grid(img):
    """Optional thin grid lines like CAD background."""
    step = 40
    for x in range(0, W, step):
        cv2.line(img, (x, 0), (x, H), (30, 30, 30), 1)
    for y in range(0, H, step):
        cv2.line(img, (0, y), (W, y), (30, 30, 30), 1)


def draw_hatched_area(img, x0, y0, x1, y1, spacing=15):
    """Diagonal hatch to mark no‑parking zones."""
    cv2.rectangle(img, (x0, y0), (x1, y1), COLOR_HATCH, 1)
    for d in range(-50, (x1 - x0) + (y1 - y0) + 50, spacing):
        p1 = (x0 + max(d, 0), y0 + max(-d, 0))
        p2 = (x0 + max(d - (y1 - y0), 0), y1 - max(d - (x1 - x0), 0))
        cv2.line(img, p1, p2, COLOR_HATCH, 1)


def draw_slots_row(img, start_x, start_y, n, slot_w, slot_h, gap, status_list):
    """Draw one horizontal row of slots."""
    for i in range(n):
        x = start_x + i * (slot_w + gap)
        y = start_y
        sid = f"S{i+1}"
        status = status_list[i] if i < len(status_list) else "free"
        color = COLOR_SLOT_FREE if status == "free" else COLOR_SLOT_OCC

        overlay = img.copy()
        cv2.rectangle(overlay, (x, y), (x + slot_w, y + slot_h), color, -1)
        img[:] = cv2.addWeighted(overlay, 0.9, img, 0.1, 0)

        cv2.rectangle(img, (x, y), (x + slot_w, y + slot_h), COLOR_BORDER, 1)

        cx, cy = x + slot_w // 2, y + slot_h // 2
        cv2.putText(img, sid, (cx - 15, cy + 5),
                    FONT, 0.4, (0, 0, 0), 1, cv2.LINE_AA)


def draw_full_map():
    img = np.zeros((H, W, 3), np.uint8)
    img[:] = COLOR_BG

    # 1) grid and outline
    draw_grid(img)
    cv2.rectangle(img, (80, 80), (W - 80, H - 80), COLOR_BORDER, 2)

    # 2) central driving lane
    lane_y = 260
    cv2.line(img, (80, lane_y), (W - 80, lane_y), COLOR_LANE, 3)
    cv2.line(img, (80, lane_y + 200), (W - 80, lane_y + 200), COLOR_LANE, 3)

    # 3) hatched (no‑parking) areas (example zones)
    draw_hatched_area(img, 80, lane_y + 10, 260, lane_y + 190)          # left block
    draw_hatched_area(img, W - 260, lane_y + 10, W - 80, lane_y + 190)  # right block

    # 4) parking slots (top row over lane)
    slot_w, slot_h, gap = 60, 100, 12
    statuses_top = ["free", "occ", "occ", "free", "free",
                    "occ", "free", "occ", "free", "occ"]
    draw_slots_row(img, 280, 120, 10, slot_w, slot_h, gap, statuses_top)

    # 5) parking slots (middle row)
    statuses_mid = ["occ" if i % 2 else "free" for i in range(10)]
    draw_slots_row(img, 280, lane_y + 20, 10, slot_w, slot_h, gap, statuses_mid)

    # 6) parking slots (bottom row)
    statuses_bot = ["free"] * 10
    draw_slots_row(img, 280, lane_y + 220, 10, slot_w, slot_h, gap, statuses_bot)

    # 7) simple legend on right
    legend_x = W - 260
    legend_y = 100
    cv2.putText(img, "Legend", (legend_x, legend_y), FONT, 0.6, COLOR_TEXT, 1, cv2.LINE_AA)
    cv2.rectangle(img, (legend_x, legend_y + 20), (legend_x + 20, legend_y + 40),
                  COLOR_SLOT_FREE, -1)
    cv2.putText(img, "Available", (legend_x + 30, legend_y + 37),
                FONT, 0.5, COLOR_TEXT, 1, cv2.LINE_AA)
    cv2.rectangle(img, (legend_x, legend_y + 50), (legend_x + 20, legend_y + 70),
                  COLOR_SLOT_OCC, -1)
    cv2.putText(img, "Occupied", (legend_x + 30, legend_y + 67),
                FONT, 0.5, COLOR_TEXT, 1, cv2.LINE_AA)

    return img


if __name__ == "__main__":
    map_img = draw_full_map()
    cv2.imwrite("hikvision_style_static_map.png", map_img)
    cv2.imshow("Hikvision-like static map", map_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
