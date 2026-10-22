import streamlit as st
import os
import sys
import json
import cv2

# Fix Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.detection import VideoProcessor

st.set_page_config(page_title="Select Location", page_icon="📍", layout="wide")

# CSS
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "../styles/main.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
load_css()

# Data
@st.cache_data
def load_locations():
    path = os.path.join(os.path.dirname(__file__), "../data/locations.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

LOCATIONS = load_locations()

# Model
@st.cache_resource
def get_vp():
    return VideoProcessor("best.pt")

vp = get_vp()

# Init State
if 'booking_flow' not in st.session_state:
    st.session_state.booking_flow = {} 

st.markdown("## 📍 Select Parking Location")

# Layout: Sidebar for selection, Main for Live View
with st.sidebar:
    st.header("Locations")
    loc_names = list(LOCATIONS.keys())
    display_names = {k: v['name'] for k, v in LOCATIONS.items()}
    
    sel_loc_key = st.selectbox(
        "Choose Venue", 
        loc_names, 
        format_func=lambda x: display_names[x]
    )
    
    loc_data = LOCATIONS[sel_loc_key]
    
    st.markdown("---")
    st.info("View the live feed on the right to spot available slots.")

# Main Area
if sel_loc_key:
    st.markdown(f"### 📹 Live Feed: {loc_data['name']}")
    
    # Process Video
    vid_src = loc_data.get('video_source', 'data/video.mp4')
    json_src = loc_data.get('json_source', 'data/video.json')
    
    frame, slot_status, free_cnt, occ_cnt = vp.get_live_frame(vid_src, json_src)
    total_slots = free_cnt + occ_cnt
    
    # Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Available", f"{free_cnt}/{total_slots}", delta="Free", delta_color="normal")
    m2.metric("Occupied", f"{occ_cnt}/{total_slots}", delta="Full", delta_color="inverse")
    
    # Video
    if frame is not None:
        frame = cv2.resize(frame, (1080, 600))
        st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), caption="Live YOLO Detection")
        
    # Slot Grid & Selection
    st.markdown("#### Available Slots")
    free_slots = [s for s, stat in slot_status.items() if stat == "Free"]
    free_slots.sort() # simple sort
    
    if free_slots:
        selected_slot = st.selectbox("Select a Slot to Book", free_slots)
        
        if st.button("PROCEED TO BOOKING ➔", type="primary"):
            st.session_state.booking_flow = {
                "location_key": sel_loc_key,
                "location_name": loc_data['name'],
                "slot": selected_slot,
                "wing": "General" # Default, can extend if needed
            }
            st.switch_page("pages/2_booking.py")
    else:
        st.error("No Slots Available at this location.")
