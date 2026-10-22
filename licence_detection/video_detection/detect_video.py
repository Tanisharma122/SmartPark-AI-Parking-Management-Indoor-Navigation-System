import cv2
import sys
import os
import easyocr
import numpy as np
from collections import Counter
from ultralytics import YOLO

# Add parent directory to path to import common_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common_utils import save_plate_to_db, init_db, clean_ocr_text

# ================= CONFIGURATION =================
# CHANGE THIS TO YOUR VIDEO FILE NAME OR USE 0 FOR WEBCAM
VIDEO_SOURCE = "v3gg.mp4" 

# Other settings
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'numberplate.pt')
CONF_THRESHOLD = 0.25
MIN_OCCURRENCE_TO_SAVE = 5 
BUFFER_SIZE = 30
# =================================================

def get_stable_plate(buffer):
    if not buffer: return None
    counts = Counter(buffer)
    most_common, frequency = counts.most_common(1)[0]
    if frequency >= MIN_OCCURRENCE_TO_SAVE:
        return most_common
    return None

def detect_video():
    # 1. Init DB
    init_db()
    
    # 2. Load Resources
    print("🔄 Loading Model and OCR...")
    model = YOLO(MODEL_PATH)
    reader = easyocr.Reader(['en'], gpu=False)
    
    # 3. Open Video Source
    print(f"▶ Opening Video Source: {VIDEO_SOURCE}")
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    
    if not cap.isOpened():
        print(f"❌ Error: Cannot open video source: {VIDEO_SOURCE}")
        print("   If using a file, make sure it is in the 'video_detection' folder.")
        return

    print("✅ Video started! Press 'q' to exit.")
    plate_buffer = []
    detected_history = [] # List to store confirmed plates for UI

    while True:
        ret, frame = cap.read()
        if not ret:
            print("End of video.")
            break
            
        # 4. Detect
        results = model.predict(source=frame, conf=CONF_THRESHOLD, save=False, verbose=False)
        
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # Draw Box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Crop & OCR
                plate_crop = frame[y1:y2, x1:x2]
                if plate_crop.size == 0: continue
                
                gray_plate = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
                ocr_results = reader.readtext(gray_plate, detail=0)
                
                if ocr_results:
                    raw_text = "".join(ocr_results)
                    candidate = clean_ocr_text(raw_text)
                    
                    if len(candidate) > 4:
                        # Add to buffer
                        plate_buffer.append(candidate)
                        if len(plate_buffer) > BUFFER_SIZE:
                            plate_buffer.pop(0)
                        
                        # Draw provisional text
                        cv2.putText(frame, candidate, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # 5. Stability Check & Save
        stable_plate = get_stable_plate(plate_buffer)
        if stable_plate:
            is_new = save_plate_to_db(stable_plate)
            
            # Add to history if unique (or just for display purposes, keep recent ones)
            if stable_plate not in detected_history:
                detected_history.insert(0, stable_plate) # Add to top
                
            # Keep history manageable
            if len(detected_history) > 10:
                detected_history.pop()

        # 6. UI Construction
        
        # A. Resize Frame for Display
        max_display_h = 800
        h, w = frame.shape[:2]
        
        scale = 1.0
        if h > max_display_h:
            scale = max_display_h / h
            
        new_w = int(w * scale)
        new_h = int(h * scale)
        display_frame = cv2.resize(frame, (new_w, new_h))
        
        # B. Create Sidebar
        sidebar_w = 300
        canvas_w = new_w + sidebar_w
        canvas_h = new_h
        
        # Create canvas (Black Background)
        canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)
        
        # Place video on left
        canvas[0:new_h, 0:new_w] = display_frame
        
        # Draw Sidebar Content
        # Header
        cv2.rectangle(canvas, (new_w, 0), (canvas_w, 80), (30, 30, 30), -1)
        cv2.putText(canvas, "DETECTED PLATES", (new_w + 20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # List Plates
        start_y = 120
        gap = 50
        
        for i, plate in enumerate(detected_history):
            # Highlight top one
            color = (255, 255, 255)
            thickness = 1
            if i == 0:
                color = (0, 255, 0) # Green for latest
                thickness = 2
                
            cv2.putText(canvas, plate, (new_w + 30, start_y + (i * gap)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, thickness)
        
        # Divider Line
        cv2.line(canvas, (new_w, 0), (new_w, canvas_h), (100, 100, 100), 2)

        # Show
        cv2.imshow("License Plate Detection System", canvas)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    detect_video()

