import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

import cv2
import numpy as np
from PIL import Image, ImageTk

# ----- CONFIG -----
IMAGE_PATH = "z_map_system_trail\other\pklotimg.jpg"  # or "z_map_system_trail/other/pklotimg.jpg"
REGIONS_JSON = "regions1.json"
MAP_OUT = "parking_map_from_regions1.png"

COLOR_BG = (10, 10, 10)      # map background (BGR)
COLOR_BORDER = (80, 80, 80)

TYPE_COLORS = {
    "lane": (0, 255, 255),       # yellow
    "slot": (0, 200, 0),         # green
    "forbidden": (0, 0, 220),    # red
}


class RegionEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Parking Map Region Editor")

        self.img_bgr = cv2.imread(IMAGE_PATH)
        if self.img_bgr is None:
            raise RuntimeError(f"Cannot read {IMAGE_PATH}")
        self.h, self.w = self.img_bgr.shape[:2]
        self.current_type = "slot"   # default region type

        self.regions = []            # list of dict: {type, x1,y1,x2,y2}

        self.start_x = None
        self.start_y = None
        self.rect_id = None

        self.build_ui()
        self.bind_events()

    def build_ui(self):
        self.canvas = tk.Canvas(self.root, width=self.w, height=self.h)
        self.canvas.grid(row=0, column=0, columnspan=4)

        self.photo = ImageTk.PhotoImage(
            Image.fromarray(cv2.cvtColor(self.img_bgr, cv2.COLOR_BGR2RGB))
        )
        self.canvas_img = self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

        tk.Label(self.root, text="Current type:").grid(row=1, column=0, sticky="e")
        self.type_label = tk.Label(self.root, text=self.current_type, fg="green")
        self.type_label.grid(row=1, column=1, sticky="w")

        tk.Button(self.root, text="Open image", command=self.load_image).grid(row=1, column=2)
        tk.Button(self.root, text="Save (JSON + Map)", command=self.save_all).grid(row=1, column=3)

        tk.Label(
            self.root,
            text="Keys: g=slot/green, r=forbidden/red, y=lane/yellow, s=save",
        ).grid(row=2, column=0, columnspan=4)

    def bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self.root.bind("g", lambda e: self.set_type("slot"))
        self.root.bind("r", lambda e: self.set_type("forbidden"))
        self.root.bind("y", lambda e: self.set_type("lane"))
        self.root.bind("s", lambda e: self.save_all())

    def set_type(self, t):
        self.current_type = t
        color = "green" if t == "slot" else "red" if t == "forbidden" else "yellow"
        self.type_label.config(text=t, fg=color)

    def load_image(self):
        path = filedialog.askopenfilename(
            title="Select parking image",
            filetypes=[("Image files", "*.jpg *.png *.jpeg *.bmp")]
        )
        if not path:
            return
        global IMAGE_PATH
        IMAGE_PATH = path
        self.img_bgr = cv2.imread(IMAGE_PATH)
        if self.img_bgr is None:
            return
        self.h, self.w = self.img_bgr.shape[:2]
        self.canvas.config(width=self.w, height=self.h)
        self.photo = ImageTk.PhotoImage(
            Image.fromarray(cv2.cvtColor(self.img_bgr, cv2.COLOR_BGR2RGB))
        )
        self.canvas.itemconfig(self.canvas_img, image=self.photo)
        self.regions.clear()
        self.redraw_regions()

    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        if self.rect_id is not None:
            self.canvas.delete(self.rect_id)
            self.rect_id = None

    def on_drag(self, event):
        if self.start_x is None or self.start_y is None:
            return
        if self.rect_id is not None:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            event.x,
            event.y,
            outline="cyan",
            width=2,
        )

    def on_release(self, event):
        if self.start_x is None or self.start_y is None:
            return
        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y
        if abs(x2 - x1) < 5 or abs(y2 - y1) < 5:
            # too small, ignore
            self.start_x = self.start_y = None
            if self.rect_id is not None:
                self.canvas.delete(self.rect_id)
                self.rect_id = None
            return

        # normalize coordinates
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])

        self.regions.append(
            {"type": self.current_type, "x1": x1, "y1": y1, "x2": x2, "y2": y2}
        )

        self.start_x = self.start_y = None
        self.redraw_regions()

    def redraw_regions(self):
        # clear old rectangles
        self.canvas.delete("region")
        for r in self.regions:
            t = r["type"]
            x1, y1, x2, y2 = r["x1"], r["y1"], r["x2"], r["y2"]

            if t == "slot":          # green border only
                outline = "green"
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, outline=outline, width=2, tags="region"
                )

            elif t == "forbidden":   # red border only
                outline = "red"
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, outline=outline, width=2, tags="region"
                )

            elif t == "lane":        # yellow border + hatch
                outline = "yellow"
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, outline=outline, width=2, tags="region"
                )
                spacing = 8
                w = x2 - x1
                h = y2 - y1
                for d in range(-h, w, spacing):
                    x_start = x1 + max(d, 0)
                    y_start = y2 - max(-d, 0)
                    x_end = x1 + max(d + h, 0)
                    y_end = y2 - max(-(d + h), 0)
                    self.canvas.create_line(
                        x_start, y_start, x_end, y_end,
                        fill="yellow", width=1, tags="region"
                    )

    def save_all(self):
        # 1) save JSON
        Path(REGIONS_JSON).write_text(
            json.dumps(self.regions, indent=2), encoding="utf-8"
        )
        print(f"Saved regions to {REGIONS_JSON}")

        # 2) generate clean CAD-style map from regions
        self.generate_map_from_regions()
        print(f"Saved map to {MAP_OUT}")

    def generate_map_from_regions(self):
        img = np.zeros((self.h, self.w, 3), np.uint8)
        img[:] = COLOR_BG

        for r in self.regions:
            t = r["type"]
            x1, y1, x2, y2 = r["x1"], r["y1"], r["x2"], r["y2"]

            if t == "slot":
                # green border only
                cv2.rectangle(img, (x1, y1), (x2, y2), TYPE_COLORS["slot"], 2)

            elif t == "forbidden":
                # red border only
                cv2.rectangle(img, (x1, y1), (x2, y2), TYPE_COLORS["forbidden"], 2)

            elif t == "lane":
                # yellow border
                cv2.rectangle(img, (x1, y1), (x2, y2), TYPE_COLORS["lane"], 2)
                # yellow hatch lines
                spacing = 8
                w = x2 - x1
                h = y2 - y1
                for d in range(-h, w, spacing):
                    x_start = x1 + max(d, 0)
                    y_start = y2 - max(-d, 0)
                    x_end = x1 + max(d + h, 0)
                    y_end = y2 - max(-(d + h), 0)
                    cv2.line(
                        img,
                        (x_start, y_start),
                        (x_end, y_end),
                        TYPE_COLORS["lane"],
                        1,
                        cv2.LINE_AA,
                    )

        cv2.imwrite(MAP_OUT, img)


if __name__ == "__main__":
    root = tk.Tk()
    app = RegionEditor(root)
    root.mainloop()
