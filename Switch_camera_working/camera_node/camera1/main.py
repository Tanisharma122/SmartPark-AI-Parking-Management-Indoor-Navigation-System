import cv2, json, time, numpy as np
from config import *
from detector import load_manager
from sender import send_data

def is_free(img, pts):
    mask = np.zeros(img.shape[:2], np.uint8)
    cv2.polylines(mask, [pts], True, 255, 2)
    px = img[mask == 255]
    if len(px) == 0:
        return False
    return (np.sum((px[:,2]>150)&(px[:,1]<120)&(px[:,0]<120))/len(px)) > 0.45

slots = json.load(open(SLOTS_JSON))

cap = cv2.VideoCapture(VIDEO_PATH)
pm = load_manager(MODEL_PATH, SLOTS_JSON, CONF_THRES, IOU_THRES)

last = 0
while True:
    ok, frame = cap.read()
    if not ok: break

    frame = cv2.resize(frame,(FRAME_WIDTH,FRAME_HEIGHT))
    res = pm(frame.copy())
    ref = res.plot_im
    draw = frame.copy()

    free_ids, results = [], []

    for s in slots:
        sid = s["slot_id"]
        pts = np.array(s["points"], np.int32)
        free = is_free(ref, pts)
        color = (0,0,255) if free else (0,255,0)

        if free:
            free_ids.append(sid)
            cx,cy = pts[:,0].mean().astype(int), pts[:,1].mean().astype(int)
            cv2.putText(draw,sid,(cx-10,cy),0,0.5,(0,0,255),2)

        cv2.polylines(draw,[pts],True,color,2)
        results.append({"slot_id":sid,"status":"free" if free else "occupied"})

    payload = {
        "camera_id": CAMERA_ID,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "slots": results
    }

    if time.time()-last>SEND_INTERVAL:
        send_data(BACKEND_URL,payload)
        last=time.time()

    cv2.imshow("Camera",draw)
    if cv2.waitKey(1)&0xFF in [27,ord('q')]: break

cap.release()
cv2.destroyAllWindows()
