import os
from pathlib import Path
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

def convert_folder_heic_to_jpg(input_dir, output_dir):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for heic_path in input_dir.rglob("*.[hH][eE][iI][cC]"):
        rel = heic_path.relative_to(input_dir)
        out_path = output_dir / rel.with_suffix(".jpg")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        img = Image.open(heic_path)
        img.convert("RGB").save(out_path, format="JPEG", quality=95)
        print("Converted:", heic_path, "->", out_path)

# example
convert_folder_heic_to_jpg("images", "jpg_images")
