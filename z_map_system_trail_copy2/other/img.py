import cv2
import time

cpt = 0
maxFrames = 1

cap = cv2.VideoCapture("pklot.mp4")  # video must be in the SAME folder as img.py
print("Video opened:", cap.isOpened())

while cpt < maxFrames:
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame")
        break

    frame = cv2.resize(frame, (1920, 1080))

    # save in the current folder as img0.jpg
    cv2.imwrite("pklotimg.jpg", frame)
    print("Saved img0.jpg")

    cpt += 1
    time.sleep(0.01)

cap.release()
cv2.destroyAllWindows()
print("Done")
