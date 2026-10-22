import cv2
import sys
import os
import easyocr
import numpy as np
from ultralytics import YOLO

# Add parent directory to path to import common_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common_utils import save_plate_to_db, init_db, clean_ocr_text

# ================= CONFIGURATION =================
# Model is in the parent directory
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'numberplate.pt')
# Default image to test if none provided
DEFAULT_IMAGE = os.path.join(os.path.dirname(__file__), 'licence-dataset/car5.png')
OUTPUT_IMAGE = "image_detection/output/output_car5.jpg"
# =================================================

def detect_and_save(image_path):
    # 1. Initialize DB
    init_db()

    # 2. Check Paths
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model not found at: {MODEL_PATH}")
        return
    if not os.path.exists(image_path):
        print(f"❌ Image not found at: {image_path}")
        return

    # 3. Load Model & OCR
    print(f"🔄 Loading Model: {MODEL_PATH}")
    model = YOLO(MODEL_PATH)
    reader = easyocr.Reader(['en'], gpu=False)

    # 4. Read Image
    frame = cv2.imread(image_path)
    if frame is None:
        print("❌ Could not read image.")
        return

    print("🔍 Analyzing Image...")
    results = model.predict(source=frame, conf=0.25, save=False, verbose=False)
    
    detected = False
    
    # 5. Process Detections
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Draw initial box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Crop
            plate_crop = frame[y1:y2, x1:x2]
            if plate_crop.size == 0: continue
            
            # OCR
            gray_plate = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
            ocr_results = reader.readtext(gray_plate, detail=0)
            
            if ocr_results:
                raw_text = "".join(ocr_results)
                plate_text = clean_ocr_text(raw_text)
                
                # Filter noise
                if len(plate_text) > 4: 
                    print(f"✅ DETECTED: {plate_text} (Raw: {raw_text})")
                    detected = True
                    
                    # Store in DB
                    save_plate_to_db(plate_text)
                    
                    # Annotate Image with Text
                    label = f"Plate: {plate_text}"
                    cv2.rectangle(frame, (x1, y1-30), (x1 + 250, y1), (0, 255, 0), -1)
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    
    # 6. Save Wrapper Output
    if not detected:
        print("⚠️ No clear license plate text detected.")
        
    cv2.imwrite(OUTPUT_IMAGE, frame)
    print(f"🖼 Output saved to: {OUTPUT_IMAGE}")
    
    # 7. Show (Optional)
    cv2.imshow("Detected License Plate", frame)
    print("Press any key to close the image window...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    img_arg = DEFAULT_IMAGE
    if len(sys.argv) > 1:
        img_arg = sys.argv[1]
    
    detect_and_save(img_arg)
