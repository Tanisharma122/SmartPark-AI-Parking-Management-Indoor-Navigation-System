import cv2
import json
import numpy as np

# image_path = "img0_1080x600.jpg"
# json_file  = "slots_cam1.json"
image_path = "2.jpg"          # your parking image
json_file = "bounding_boxes.json" 

img = cv2.imread(image_path)
assert img is not None
h, w = img.shape[:2]
print("Image size:", w, "x", h)

with open(json_file, "r", encoding="utf-8") as f:
    regions = json.load(f)

for i, region in enumerate(regions, start=1):
    pts = np.array(region["points"], dtype=np.int32)
    cv2.polylines(img, [pts], True, (0, 255, 0), 2)
    cx = int(np.mean(pts[:, 0]))
    cy = int(np.mean(pts[:, 1]))
    cv2.circle(img, (cx, cy), 4, (0, 0, 255), -1)
    cv2.putText(img, f"S{i}", (cx + 5, cy - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

cv2.imshow("Check polygons only", img)
cv2.waitKey(0)
cv2.destroyAllWindows()
