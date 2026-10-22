import streamlit as st
from ultralytics import YOLO
import cv2
import numpy as np
import json
import os
import time

# 🔥 BACKEND CONFIG - VIDEO PATHS AT TOP
IMG_WIDTH, IMG_HEIGHT = 1080, 600
MODEL_PATH = 'models/best.pt'
JSON_PATH = 'data/video.json'

# VIDEO PATHS - EDIT HERE
VIDEO_PATHS = 'data/video.mp4'

st.title("🔴 LIVE Parking Detection")

@st.cache_resource
def load_model():
    return YOLO(MODEL_PATH)

model = load_model()

def load_json():
    with open(JSON_PATH, 'r') as f:
        return json.load(f)

dataset = load_json()

# Sidebar - Video paths from config
st.sidebar.header("📹 Video Source")
video_file = st.sidebar.selectbox("Select Video", list(VIDEO_PATHS.keys()))
location = VIDEO_PATHS[video_file]

slot_coords = dataset[location]['slots']

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📺 Video Preview")
    st.video(video_file)

with col2:
    st.subheader("🎯 LIVE Detection")
    frame_ph = st.empty()
    stats_ph = st.empty()
    
    while True:
        # Extract frame from video
        cap = cv2.VideoCapture(video_file)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 3)
        ret, frame = cap.read()
        cap.release()
        
        frame = cv2.resize(frame, (IMG_WIDTH, IMG_HEIGHT))
        
        # YOLO Detection
        results = model(frame, verbose=False)
        annotated = results[0].plot()
        
        # JSON Slot Matching
        free_slots, occupied_slots = 0, 0
        
        for slot_id, coords in slot_coords.items():
            pts = np.array(coords, np.int32).reshape((-1, 1, 2))
            
            # Check YOLO overlap
            slot_free = True
            slot_center_x = int(np.mean([p[0] for p in coords]))
            slot_center_y = int(np.mean([p[1] for p in coords]))
            
            for box in results[0].boxes:
                if int(box.cls) == 1:  # occupied
                    x1,y1,x2,y2 = box.xyxy[0].cpu().numpy().astype(int)
                    if x1 < slot_center_x < x2 and y1 < slot_center_y < y2:
                        slot_free = False
                        break
            
            color = (0,255,0) if slot_free else (0,0,255)
            cv2.polylines(annotated, [pts], True, color, 3)
            cv2.putText(annotated, slot_id, (pts[0][0][0], pts[0][0][1]-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            free_slots += slot_free
            occupied_slots += not slot_free
        
        frame_ph.image(annotated, use_column_width=True)
        
        col1, col2 = stats_ph.columns(2)
        col1.metric("🟢 FREE", free_slots)
        col2.metric("🔴 OCCUPIED", occupied_slots)
        
        time.sleep(2)
        st.rerun()
