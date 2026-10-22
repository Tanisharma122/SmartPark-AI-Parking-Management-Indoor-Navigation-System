import cv2
import numpy as np
import json
import os
from ultralytics import YOLO
import streamlit as st

class VideoProcessor:
    def __init__(self, model_path="best.pt"):
        # Load Model
        self.model_path = model_path
        if not os.path.exists(model_path):
             # Try absolute path from current CWD if relative fails
             self.model_path = os.path.abspath("best.pt")
        
        try:
            self.model = YOLO(self.model_path)
        except Exception as e:
            st.error(f"Error loading model {self.model_path}: {e}")
            self.model = None

    def get_live_frame(self, video_path, json_path):
        """
        Reads one frame from video (simulating live feed loop),
        Runs YOLO,
        Overlays Polygons from JSON.
        """
        if not os.path.exists(video_path):
            return None, {}, 0, 0

        # Read JSON
        polygons = []
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
                # Parse depending on JSON structure
                # Structure seen: list of dicts with "id"/"slot_id" and "points" (list of lists)
                for item in data:
                    pid = item.get("id") or item.get("slot_id")
                    pts = item.get("points")
                    if pid and pts:
                        polygons.append({"id": pid, "points": np.array(pts, np.int32)})
        
        # Read Video
        cap = cv2.VideoCapture(video_path)
        # Random seek to simulate "Live" if needed, or just read first frame for speed in Streamlit
        # To make it look "Live" in Streamlit loop, we usually rely on st.rerun or looping inside component
        # Here we just read a frame.
        
        # For better "Live" feel, let's skip to a random frame or keep state?
        # Keeping state in class is hard across Streamlit reruns without session_state.
        # We will just read a random frame to simulate movement for now.
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames > 0:
            random_frame = np.random.randint(0, total_frames)
            cap.set(cv2.CAP_PROP_POS_FRAMES, random_frame)
            
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return None, {}, 0, 0

        # Run YOLO
        if self.model:
            results = self.model(frame, verbose=False, iou=0.4, conf=0.25)
            boxes = results[0].boxes.xywh.cpu().numpy() # x_center, y_center, w, h
        else:
            boxes = []

        slot_status = {}
        occupied_count = 0
        total_slots = len(polygons)

        # Draw & Check Occupancy
        overlay = frame.copy()
        
        for poly in polygons:
            s_id = poly["id"]
            pts = poly["points"]
            
            is_occupied = False
            
            # Check intersection with ANY detected car
            # Simple Logic: If Car Center is inside Polygon
            for box in boxes:
                x, y, w, h = box
                # Check point polygon test
                # Measure dist is positive if inside, negative if outside
                dist = cv2.pointPolygonTest(pts, (x, y), False)
                if dist >= 0:
                    is_occupied = True
                    break
            
            slot_status[s_id] = "Occupied" if is_occupied else "Free"
            
            # Color Logic
            color = (0, 0, 255) if is_occupied else (0, 255, 0) # BGR: Red/Green
            if is_occupied:
                occupied_count += 1

            # Draw
            cv2.polylines(overlay, [pts], True, color, 2)
            cv2.fillPoly(overlay, [pts], color)
            
            # Text Center
            M = cv2.moments(pts)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                cv2.putText(overlay, s_id, (cX - 10, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # Blend
        alpha = 0.4
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        
        return frame, slot_status, len(polygons) - occupied_count, occupied_count
