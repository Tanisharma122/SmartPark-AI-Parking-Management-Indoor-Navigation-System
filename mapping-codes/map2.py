import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

import cv2
import numpy as np
from PIL import Image, ImageTk

# ----- CONFIG -----
IMAGE_PATH = "z_map_system_trail\other\pklotimg.jpg"
REGIONS_JSON = "regions.json"
MAP_OUT = "map2.png"

# Map background and borders (BGR)
COLOR_BG = (25, 25, 30)
COLOR_FRAME = (255, 255, 255)          # white outer border

# Region colors (BGR)
COLOR_BOX_ORANGE = (0, 180, 255)       # light orange for slot/forbidden borders
COLOR_LANE = (0, 230, 230)             # yellow for lanes

COLOR_DOT_SLOT = (0, 255, 0)           # green dot
COLOR_DOT_FORBID = (0, 0, 255)         # red dot
COLOR_DOT_BORDER = (255, 255, 255)     # white dot outline


class RegionEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Parking Map Region Editor")

        self.img_bgr = cv2.imread(IMAGE_PATH)
        if self.img_bgr is None:
            raise RuntimeError(f"Cannot read {IMAGE_PATH}")
        self.h, self.w = self.img_bgr.shape[:2]

        self.current_type = "slot"   # slot / forbidden / lane / arrow
        self.regions = []            # boxes (slot, forbidden, lane)
        self.arrows = []             # list of {x1,y1,x2,y2}

        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.arrow_id = None

        self.slot_counter = 1        # for A1, A2, ...
        self.arrow_mode = False

        self.build_ui()
        self.bind_events()

    # ---------- UI / events ----------

    def build_ui(self):
        # canvas area (left)
        self.canvas = tk.Canvas(self.root, width=self.w, height=self.h)
        self.canvas.grid(row=0, column=0, columnspan=4)

        self.photo = ImageTk.PhotoImage(
            Image.fromarray(cv2.cvtColor(self.img_bgr, cv2.COLOR_BGR2RGB))
        )
        self.canvas_img = self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

        # right panel: current type + list of regions
        right_frame = tk.Frame(self.root)
        right_frame.grid(row=0, column=4, sticky="ns")

        tk.Label(right_frame, text="Current type:").pack(anchor="w")
        self.type_label = tk.Label(right_frame, text=self.current_type, fg="green")
        self.type_label.pack(anchor="w", pady=(0, 8))

        tk.Button(right_frame, text="Open image", command=self.load_image).pack(fill="x", pady=2)
        tk.Button(right_frame, text="Save (JSON + Map)", command=self.save_all).pack(fill="x", pady=2)

        tk.Label(
            right_frame,
            text="Keys:\n"
                 " g = slot (orange box + green dot)\n"
                 " r = forbidden (orange box + red dot)\n"
                 " y = lane (yellow hatch)\n"
                 " a = arrow mode\n"
                 " s = save",
            justify="left",
        ).pack(anchor="w", pady=6)

        tk.Label(right_frame, text="Regions:").pack(anchor="w")
        self.listbox = tk.Listbox(right_frame, width=30, height=20)
        self.listbox.pack(fill="both", expand=True, pady=(0, 10))

    def bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self.root.bind("g", lambda e: self.set_type("slot"))
        self.root.bind("r", lambda e: self.set_type("forbidden"))
        self.root.bind("y", lambda e: self.set_type("lane"))
        self.root.bind("a", lambda e: self.set_type("arrow"))
        self.root.bind("s", lambda e: self.save_all())

    def set_type(self, t):
        self.current_type = t
        self.arrow_mode = (t == "arrow")
        if t == "slot":
            color = "green"
        elif t == "forbidden":
            color = "red"
        elif t == "lane":
            color = "yellow"
        else:
            color = "cyan"
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
        self.arrows.clear()
        self.slot_counter = 1
        self.redraw_regions()
        self.refresh_listbox()

    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        if self.rect_id is not None:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
        if self.arrow_id is not None:
            self.canvas.delete(self.arrow_id)
            self.arrow_id = None

    def on_drag(self, event):
        if self.start_x is None or self.start_y is None:
            return
        if self.arrow_mode:
            if self.arrow_id is not None:
                self.canvas.delete(self.arrow_id)
            self.arrow_id = self.canvas.create_line(
                self.start_x, self.start_y, event.x, event.y,
                arrow=tk.LAST, fill="cyan", width=2, tags="region"
            )
        else:
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
        if abs(x2 - x1) < 5 and abs(y2 - y1) < 5:
            self.start_x = self.start_y = None
            return

        if self.arrow_mode:
            self.arrows.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2})
        else:
            x1, x2 = sorted([x1, x2])
            y1, y2 = sorted([y1, y2])

            region_id = None
            if self.current_type in ("slot", "forbidden"):
                region_id = f"A{self.slot_counter}"
                self.slot_counter += 1

            self.regions.append(
                {
                    "type": self.current_type,
                    "id": region_id,
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                }
            )

        self.start_x = self.start_y = None
        if self.rect_id is not None:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
        if self.arrow_id is not None:
            self.canvas.delete(self.arrow_id)
            self.arrow_id = None

        self.redraw_regions()
        self.refresh_listbox()

    # ---------- TK preview drawing ----------

    def redraw_regions(self):
        self.canvas.delete("region")
        # preview boxes
        for r in self.regions:
            t = r["type"]
            x1, y1, x2, y2 = r["x1"], r["y1"], r["x2"], r["y2"]
            cid = r.get("id")

            if t in ("slot", "forbidden"):
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, outline="#ffb366", width=2, tags="region"
                )
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                dot_color = "green" if t == "slot" else "red"
                self.canvas.create_oval(
                    cx - 5, cy - 5, cx + 5, cy + 5,
                    fill=dot_color, outline="white", width=1, tags="region"
                )
                if cid:
                    self.canvas.create_text(
                        x2 + 10, y1 + 10, text=cid,
                        fill="white", anchor="w", tags="region"
                    )

            elif t == "lane":
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, outline="yellow", width=2, tags="region"
                )
                spacing = 8
                w = x2 - x1
                h = y2 - y1
                for d in range(0, w + h, spacing):
                    xs = x1 + max(d - h, 0)
                    ys = y1 + min(d, h)
                    xe = x1 + min(d, w)
                    ye = y1 + max(d - w, 0)
                    self.canvas.create_line(
                        xs, ys, xe, ye,
                        fill="yellow", width=1, tags="region"
                    )

        # preview arrows
        for a in self.arrows:
            self.canvas.create_line(
                a["x1"], a["y1"], a["x2"], a["y2"],
                arrow=tk.LAST, fill="cyan", width=2, tags="region"
            )

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for r in self.regions:
            t = r["type"]
            cid = r.get("id") or "-"
            self.listbox.insert(tk.END, f"{cid} [{t}]  ({r['x1']},{r['y1']})-({r['x2']},{r['y2']})")
        for i, a in enumerate(self.arrows, start=1):
            self.listbox.insert(
                tk.END, f"Arrow{i} [arrow] ({a['x1']},{a['y1']})-({a['x2']},{a['y2']})"
            )

    # ---------- Save + map generation ----------

    def save_all(self):
        # save JSON
        data = {
            "regions": self.regions,
            "arrows": self.arrows,
        }
        Path(REGIONS_JSON).write_text(json.dumps(data, indent=2), encoding="utf-8")
        print("Saved regions:")
        for r in self.regions:
            print(" ", r)
        print("Saved arrows:")
        for a in self.arrows:
            print(" ", a)

        # generate map
        self.generate_map_from_regions()
        print(f"Saved map to {MAP_OUT}")

    def generate_map_from_regions(self):
        img = np.zeros((self.h, self.w, 3), np.uint8)
        img[:] = COLOR_BG

        # white outer border
        cv2.rectangle(img, (10, 10), (self.w - 10, self.h - 10), COLOR_FRAME, 2)

        # small white squares at corners of outer border
        s = 6
        corners = [
            (10, 10),
            (self.w - 10, 10),
            (10, self.h - 10),
            (self.w - 10, self.h - 10),
        ]
        for (cx, cy) in corners:
            cv2.rectangle(img, (cx - s, cy - s), (cx + s, cy + s), COLOR_FRAME, -1)

        # draw regions
        for r in self.regions:
            t = r["type"]
            x1, y1, x2, y2 = r["x1"], r["y1"], r["x2"], r["y2"]
            cid = r.get("id")

            if t in ("slot", "forbidden"):
                cv2.rectangle(img, (x1, y1), (x2, y2), COLOR_BOX_ORANGE, 2)
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                dot_color = COLOR_DOT_SLOT if t == "slot" else COLOR_DOT_FORBID
                cv2.circle(img, (cx, cy), 6, dot_color, -1, cv2.LINE_AA)
                cv2.circle(img, (cx, cy), 6, COLOR_DOT_BORDER, 1, cv2.LINE_AA)
                if cid:
                    cv2.putText(
                        img, cid, (x2 + 5, y1 + 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                        (220, 220, 220), 1, cv2.LINE_AA
                    )

            elif t == "lane":
                cv2.rectangle(img, (x1, y1), (x2, y2), COLOR_LANE, 2)
                spacing = 8
                w = x2 - x1
                h = y2 - y1
                for d in range(0, w + h, spacing):
                    xs = x1 + max(d - h, 0)
                    ys = y1 + min(d, h)
                    xe = x1 + min(d, w)
                    ye = y1 + max(d - w, 0)
                    cv2.line(
                        img,
                        (xs, ys),
                        (xe, ye),
                        COLOR_LANE,
                        1,
                        cv2.LINE_AA,
                    )
                # small yellow squares at lane corners
                ls = 4
                for (cx, cy) in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
                    cv2.rectangle(
                        img,
                        (cx - ls, cy - ls),
                        (cx + ls, cy + ls),
                        COLOR_LANE,
                        -1,
                    )

        # draw arrows
        for a in self.arrows:
            cv2.arrowedLine(
                img,
                (a["x1"], a["y1"]),
                (a["x2"], a["y2"]),
                (200, 200, 255),
                2,
                tipLength=0.03,
            )

        cv2.imwrite(MAP_OUT, img)


if __name__ == "__main__":
    root = tk.Tk()
    app = RegionEditor(root)
    root.mainloop()
