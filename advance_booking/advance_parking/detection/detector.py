import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image, ImageDraw, ImageFont
import json
import os
from shapely.geometry import Polygon, box

class ParkingSlotDetector:
    def __init__(self, model_path="models/best.pt"):
        self.model_path = model_path
        try:
            self.model = YOLO(model_path)
            self.model.conf = 0.45  # Tuned confidence
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None
    
    def load_slot_coords(self, json_path):
        """Load slot polygon coordinates and normalize to dict"""
        if not os.path.exists(json_path):
            return {}
        
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        # Handle the list format from the new JSON
        if isinstance(data, list):
            slots = {}
            for i, slot_data in enumerate(data):
                # ID generation: S1, S2, ...
                slot_id = f"S{i+1}"
                if "points" in slot_data:
                    # JSON points are [[x,y], [x,y]...]
                    slots[slot_id] = slot_data["points"]
                else:
                    slots[slot_id] = slot_data
            return slots
            
        return data
    
    def detect_slots(self, image_path, json_path):
        """
        Detects occupied slots using Global Inference + Polygon Intersection.
        This is significantly more accurate than cropping.
        """
        if self.model is None:
            return {}
            
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            return {}
            
        # 1. Run YOLO on the FULL image
        results = self.model(img, verbose=False)
        
        detected_boxes = []
        for r in results:
            if r.boxes:
                for box_data in r.boxes:
                    # Get box coordinates [x1, y1, x2, y2]
                    xyxy = box_data.xyxy[0].tolist()
                    conf = float(box_data.conf[0])
                    
                    # Store robust detections
                    if conf > 0.4:
                        # Create a Shapely Box for the car
                        detected_boxes.append(box(xyxy[0], xyxy[1], xyxy[2], xyxy[3]))

        # 2. Check Overlap with Slots
        slots = self.load_slot_coords(json_path)
        slot_status = {}
        
        for slot_id, points in slots.items():
            try:
                # Create Polygon for the slot
                slot_poly = Polygon(points)
                
                is_occupied = False
                for car_box in detected_boxes:
                    # Check for intersection
                    if slot_poly.intersects(car_box):
                        intersection_area = slot_poly.intersection(car_box).area
                        slot_area = slot_poly.area
                        
                        # Threshold: If intersection covers > 40% of the slot
                        # OR if it covers a significant portion of the car (e.g. car is inside)
                        if (intersection_area / slot_area) > 0.45:
                            is_occupied = True
                            break
                            
                slot_status[slot_id] = "occupied" if is_occupied else "free"
            except Exception as e:
                print(f"Error processing slot {slot_id}: {e}")
                slot_status[slot_id] = "error"
        
        return slot_status
    
    def visualize_detection(self, image_path, json_path, slot_status):
        """Draw boxes on image"""
        img = cv2.imread(image_path)
        if img is None:
            return Image.new('RGB', (640, 480), color='gray')
            
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        
        slots = self.load_slot_coords(json_path)
        
        try:
            font = ImageFont.truetype("arial.ttf", 25)
        except:
            font = None

        for slot_id, status in slot_status.items():
            if slot_id not in slots: continue
            
            points = np.array(slots[slot_id], np.int32)
            points_tuple = [tuple(x) for x in points]
            
            color = (0, 255, 0) if status == "free" else (255, 0, 0) # Green/Red
            
            # Draw polygon
            draw.polygon(points_tuple, outline=color, width=4)
            
            # Calculate center for label
            M = cv2.moments(points)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
            else:
                cX, cY = points[0][0], points[0][1]
            
            # Label
            draw.text((cX-15, cY-10), str(slot_id), fill=color, font=font, stroke_width=2, stroke_fill="black")
        
        return img_pil
