import cv2
import math

IMAGE_PATH = "2.jpg"

# === 1. define nodes exactly as in your code ===
nodes = {
    "E":  (1000, 2000),
    "N1": (800,  1500),
    "N2": (600,  1200),
}

entry_node = "E"
path_nodes = ['E', 'N1', 'N2']          # from your print
route_points = [nodes[n] for n in path_nodes]

# === 2. load image and draw ONLY route + nodes ===
img = cv2.imread(IMAGE_PATH)
h, w = img.shape[:2]
print("Image size:", w, h)

# check coordinates are inside image
for name, (x, y) in nodes.items():
    print(name, x, y, "inside:", 0 <= x < w and 0 <= y < h)

im0 = img.copy()

# draw path
for i in range(len(route_points) - 1):
    x1, y1 = map(int, route_points[i])
    x2, y2 = map(int, route_points[i + 1])
    cv2.line(im0, (x1, y1), (x2, y2), (0, 255, 255), 6)

# draw nodes + labels
for name, (x, y) in nodes.items():
    x, y = int(x), int(y)
    cv2.circle(im0, (x, y), 8, (0, 0, 255), -1)
    cv2.putText(im0, name, (x + 10, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

cv2.imshow("DEBUG_ROUTE", im0)
cv2.imwrite("debug_route.jpg", im0)
cv2.waitKey(0)
cv2.destroyAllWindows()
