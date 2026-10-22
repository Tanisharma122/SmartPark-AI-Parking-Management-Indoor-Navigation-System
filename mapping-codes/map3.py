import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import cv2
import numpy as np
from PIL import Image, ImageTk

# ---------- CONFIG ----------
IMAGE_PATH = "z_map_system_trail\other\pklotimg.jpg"  # or "z_map_system_trail/other/pklotimg.jpg"
REGIONS_JSON = "regions.json"
MAP_OUT = "map3.png"
SLOT_INFO_JSON = "slot_info.json"  # slot_id -> {user, plate, uid, ...}

COLOR_BG = (25, 25, 30)
COLOR_FRAME = (255, 255, 255)

COLOR_BOX_ORANGE = (0, 180, 255)
COLOR_LANE = (0, 230, 230)
COLOR_WHITE_LINE = (220, 220, 220)

COLOR_DOT_SLOT = (0, 255, 0)
COLOR_DOT_FORBID = (0, 0, 255)
COLOR_DOT_BORDER = (255, 255, 255)


class MapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Parking Map Editor & Viewer")

        self.img_bgr = cv2.imread(IMAGE_PATH)
        if self.img_bgr is None:
            raise RuntimeError(f"Cannot read {IMAGE_PATH}")
        self.h, self.w = self.img_bgr.shape[:2]

        # Resize root window so full image fits
        self.root.geometry(f"{self.w + 380}x{self.h + 40}")

        self.current_type = "slot"  # slot/forbidden/lane/arrow/white
        self.regions = []           # boxes & lanes
        self.arrows = []            # arrows
        self.lines = []             # white lines

        self.start_x = None
        self.start_y = None
        self.temp_id = None

        self.slot_counter = 1
        self.arrow_mode = False
        self.white_line_mode = False

        self.slot_info = self.load_slot_info()

        self.build_ui()
        self.bind_events()
        self.redraw_canvas()
        self.refresh_listbox()
        self.update_map_image()

    # ---------- basic IO ----------

    def load_slot_info(self):
        p = Path(SLOT_INFO_JSON)
        if not p.exists():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))

    def save_all_json(self):
        data = {
            "regions": self.regions,
            "arrows": self.arrows,
            "lines": self.lines,
        }
        Path(REGIONS_JSON).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load_all_json(self):
        p = Path(REGIONS_JSON)
        if not p.exists():
            return
        data = json.loads(p.read_text(encoding="utf-8"))
        self.regions = data.get("regions", [])
        self.arrows = data.get("arrows", [])
        self.lines = data.get("lines", [])
        self.slot_counter = 1 + sum(1 for r in self.regions if r["type"] in ("slot", "forbidden"))

    # ---------- UI ----------

    def build_ui(self):
        # Canvas with full image
        self.canvas = tk.Canvas(self.root, width=self.w, height=self.h)
        self.canvas.grid(row=0, column=0, columnspan=4)

        self.photo = ImageTk.PhotoImage(
            Image.fromarray(cv2.cvtColor(self.img_bgr, cv2.COLOR_BGR2RGB))
        )
        self.canvas_img = self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

        # Right panel
        right = tk.Frame(self.root)
        right.grid(row=0, column=4, sticky="ns")

        tk.Label(right, text="Current mode:").pack(anchor="w")
        self.type_label = tk.Label(right, text=self.current_type, fg="green")
        self.type_label.pack(anchor="w", pady=(0, 6))

        tk.Button(right, text="Open image", command=self.load_image).pack(fill="x", pady=2)
        tk.Button(right, text="Save (JSON + Map)", command=self.save_and_render).pack(fill="x", pady=2)
        tk.Button(right, text="Reload map data", command=self.reload_from_json).pack(fill="x", pady=2)

        tk.Label(
            right,
            text=(
                "Keys:\n"
                " g = slot (orange box + green dot)\n"
                " r = forbidden (orange box + red dot)\n"
                " y = lane (yellow hatch)\n"
                " a = arrow mode\n"
                " w = white line mode\n"
                " s = save"
            ),
            justify="left",
        ).pack(anchor="w", pady=6)

        tk.Label(right, text="Regions / Lines / Arrows:").pack(anchor="w")
        self.listbox = tk.Listbox(right, width=34, height=16)
        self.listbox.pack(fill="both", expand=True, pady=(0, 10))

        tk.Label(right, text="Selected slot info:").pack(anchor="w")
        self.info_text = tk.Text(right, width=34, height=6, state="disabled")
        self.info_text.pack(fill="x", pady=(0, 10))

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
        self.root.geometry(f"{self.w + 380}x{self.h + 40}")
        self.canvas.config(width=self.w, height=self.h)
        self.photo = ImageTk.PhotoImage(
            Image.fromarray(cv2.cvtColor(self.img_bgr, cv2.COLOR_BGR2RGB))
        )
        self.canvas.itemconfig(self.canvas_img, image=self.photo)

        self.regions.clear()
        self.arrows.clear()
        self.lines.clear()
        self.slot_counter = 1
        self.redraw_canvas()
        self.refresh_listbox()
        self.update_map_image()

    def bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-1>", self.on_click_for_info)  # click dots

        self.root.bind("g", lambda e: self.set_type("slot"))
        self.root.bind("r", lambda e: self.set_type("forbidden"))
        self.root.bind("y", lambda e: self.set_type("lane"))
        self.root.bind("a", lambda e: self.set_type("arrow"))
        self.root.bind("w", lambda e: self.set_type("white"))
        self.root.bind("s", lambda e: self.save_and_render())

    def set_type(self, t):
        self.current_type = t
        self.arrow_mode = (t == "arrow")
        self.white_line_mode = (t == "white")
        if t == "slot":
            color = "green"
        elif t == "forbidden":
            color = "red"
        elif t == "lane":
            color = "yellow"
        elif t == "white":
            color = "white"
        else:
            color = "cyan"
        self.type_label.config(text=t, fg=color)

    # ---------- mouse interaction ----------

    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        if self.temp_id is not None:
            self.canvas.delete(self.temp_id)
            self.temp_id = None

    def on_drag(self, event):
        if self.start_x is None or self.start_y is None:
            return
        if self.temp_id is not None:
            self.canvas.delete(self.temp_id)

        if self.arrow_mode or self.white_line_mode:
            self.temp_id = self.canvas.create_line(
                self.start_x,
                self.start_y,
                event.x,
                event.y,
                fill="white" if self.white_line_mode else "cyan",
                width=2,
            )
        else:
            self.temp_id = self.canvas.create_rectangle(
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

        if self.arrow_mode or self.white_line_mode:
            entry = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
            if self.white_line_mode:
                self.lines.append(entry)
            else:
                self.arrows.append(entry)
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
        if self.temp_id is not None:
            self.canvas.delete(self.temp_id)
            self.temp_id = None

        self.redraw_canvas()
        self.refresh_listbox()
        self.update_map_image()

    # click dot → show info
    def on_click_for_info(self, event):
        x, y = event.x, event.y
        clicked_id = None
        for r in self.regions:
            if r["type"] not in ("slot", "forbidden"):
                continue
            cx = (r["x1"] + r["x2"]) // 2
            cy = (r["y1"] + r["y2"]) // 2
            if (x - cx) ** 2 + (y - cy) ** 2 <= 10 ** 2:
                clicked_id = r.get("id")
                break

        if clicked_id:
            info = self.slot_info.get(clicked_id, None)
            self.info_text.config(state="normal")
            self.info_text.delete("1.0", tk.END)
            if info:
                self.info_text.insert(
                    tk.END,
                    f"Slot: {clicked_id}\n"
                    f"User: {info.get('user','-')}\n"
                    f"Plate: {info.get('plate','-')}\n"
                    f"UID: {info.get('uid','-')}\n",
                )
            else:
                self.info_text.insert(tk.END, f"Slot: {clicked_id}\nNo user info.\n")
            self.info_text.config(state="disabled")

    # ---------- drawing & list ----------

    def redraw_canvas(self):
        self.canvas.delete("overlay")
        for r in self.regions:
            t = r["type"]
            x1, y1, x2, y2 = r["x1"], r["y1"], r["x2"], r["y2"]
            cid = r.get("id")
            if t in ("slot", "forbidden"):
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline="#ffb366", width=2, tags="overlay"
                )
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                dot_color = "green" if t == "slot" else "red"
                self.canvas.create_oval(
                    cx - 6, cy - 6, cx + 6, cy + 6,
                    fill=dot_color, outline="white", width=1, tags="overlay"
                )
                if cid:
                    self.canvas.create_text(
                        x2 + 10, y1 + 10, text=cid,
                        fill="white", anchor="w", tags="overlay"
                    )
            elif t == "lane":
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, outline="yellow", width=2, tags="overlay"
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
                        xs, ys, xe, ye, fill="yellow", width=1, tags="overlay"
                    )
        for line in self.lines:
            self.canvas.create_line(
                line["x1"], line["y1"], line["x2"], line["y2"],
                fill="white", width=2, tags="overlay"
            )
        for a in self.arrows:
            self.canvas.create_line(
                a["x1"], a["y1"], a["x2"], a["y2"],
                arrow=tk.LAST, fill="cyan", width=2, tags="overlay"
            )

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for r in self.regions:
            cid = r.get("id") or "-"
            self.listbox.insert(
                tk.END,
                f"{cid} [{r['type']}] ({r['x1']},{r['y1']})-({r['x2']},{r['y2']})"
            )
        for i, line in enumerate(self.lines, start=1):
            self.listbox.insert(
                tk.END,
                f"WhiteLine{i} [white] ({line['x1']},{line['y1']})-({line['x2']},{line['y2']})"
            )
        for i, a in enumerate(self.arrows, start=1):
            self.listbox.insert(
                tk.END,
                f"Arrow{i} [arrow] ({a['x1']},{a['y1']})-({a['x2']},{a['y2']})"
            )

    # ---------- map rendering ----------

    def save_and_render(self):
        self.save_all_json()
        self.update_map_image()
        messagebox.showinfo("Saved", f"JSON -> {REGIONS_JSON}\nMap -> {MAP_OUT}")

    def reload_from_json(self):
        self.load_all_json()
        self.redraw_canvas()
        self.refresh_listbox()
        self.update_map_image()

    def update_map_image(self):
        img = np.zeros((self.h, self.w, 3), np.uint8)
        img[:] = COLOR_BG

        # outer frame
        cv2.rectangle(img, (10, 10), (self.w - 10, self.h - 10), COLOR_FRAME, 2)

        # corner squares
        s = 6
        for (cx, cy) in [
            (10, 10),
            (self.w - 10, 10),
            (10, self.h - 10),
            (self.w - 10, self.h - 10),
        ]:
            cv2.rectangle(img, (cx - s, cy - s), (cx + s, cy + s), COLOR_FRAME, -1)

        # white lines
        for line in self.lines:
            cv2.line(
                img,
                (line["x1"], line["y1"]),
                (line["x2"], line["y2"]),
                COLOR_WHITE_LINE,
                2,
                cv2.LINE_AA,
            )

        # regions
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
                        img, (xs, ys), (xe, ye), COLOR_LANE, 1, cv2.LINE_AA
                    )

        # arrows
        for a in self.arrows:
            cv2.arrowedLine(
                img,
                (a["x1"], a["y1"]),
                (a["x2"], a["y2"]),
                (200, 200, 255),
                2,
                tipLength=0.03,
            )

        # legend
        font = cv2.FONT_HERSHEY_SIMPLEX
        lx, ly, lh = 20, 30, 18
        cv2.putText(img, "Legend:", (lx, ly), font, 0.5, (220, 220, 220), 1, cv2.LINE_AA)
        cv2.putText(img, "g: Slot (orange + green dot)", (lx, ly + lh),
                    font, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
        cv2.putText(img, "r: Forbidden (orange + red dot)", (lx, ly + 2*lh),
                    font, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
        cv2.putText(img, "y: Lane (yellow hatch)", (lx, ly + 3*lh),
                    font, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
        cv2.putText(img, "w: White line", (lx, ly + 4*lh),
                    font, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
        cv2.putText(img, "a: Arrow", (lx, ly + 5*lh),
                    font, 0.45, (200, 200, 200), 1, cv2.LINE_AA)

        cv2.imwrite(MAP_OUT, img)


if __name__ == "__main__":
    root = tk.Tk()
    app = MapApp(root)
    root.mainloop()
