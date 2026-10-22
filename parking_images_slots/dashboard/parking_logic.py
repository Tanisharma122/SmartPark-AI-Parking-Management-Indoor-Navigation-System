import os
import uuid
from PIL import Image, ImageDraw  # pip install pillow

def analyze_parking_image(image_path, results_folder):
    """
    image_path: path to uploaded image.
    results_folder: folder where annotated image should be stored.
    Returns a dict with slot stats and filename of annotated image.
    """

    # 1) Load image
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    # 2) Dummy logic for now: assume 4 slots, 2 free, 2 occupied
    #    Later you will replace this with your YOLO + slot mapping.
    slots = [
        {"id": "A1", "status": "free"},
        {"id": "A2", "status": "occupied"},
        {"id": "A3", "status": "free"},
        {"id": "A4", "status": "occupied"},
    ]

    # Draw dummy boxes so UI can show something
    w, h = img.size
    box_w, box_h = w // 4, h // 10
    colors = {"free": "green", "occupied": "red"}

    for i, slot in enumerate(slots):
        x1 = 10 + i * (box_w + 10)
        y1 = 10
        x2 = x1 + box_w
        y2 = y1 + box_h
        draw.rectangle([x1, y1, x2, y2], outline=colors[slot["status"]], width=3)
        draw.text((x1 + 5, y1 + 5), slot["id"], fill=colors[slot["status"]])

    # 3) Save annotated image
    out_name = f"annotated_{uuid.uuid4().hex[:8]}.png"
    out_path = os.path.join(results_folder, out_name)
    img.save(out_path)

    total_slots = len(slots)
    free_slots = sum(1 for s in slots if s["status"] == "free")
    occupied_slots = total_slots - free_slots

    return {
        "annotated_filename": out_name,
        "total_slots": total_slots,
        "free_slots": free_slots,
        "occupied_slots": occupied_slots,
        "slots": slots
    }
