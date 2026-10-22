# SRC = "jpg_images/2.jpg"   # your raw image
# DST = "2.jpg"   # new resized image

import cv2

SRC = "images/3.jpg"   # your raw image
DST = "3.jpg"   # new resized image

FRAME_WIDTH = 1080
FRAME_HEIGHT = 600

img = cv2.imread(SRC)
assert img is not None, "Error loading source image"

resized = cv2.resize(img, (FRAME_WIDTH, FRAME_HEIGHT))
cv2.imwrite(DST, resized)
print("Saved:", DST)

