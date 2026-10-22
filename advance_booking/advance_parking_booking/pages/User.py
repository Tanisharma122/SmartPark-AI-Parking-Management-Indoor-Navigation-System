import streamlit as st
import os
import sys

# -- PATH FIX --
# Allows running this file directly or via pages/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import cv2
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

# -- BACKEND --
from backend.video_processor import VideoProcessor

# -- SETUP --
st.set_page_config(page_title="User Booking", layout="wide", page_icon="🅿️")

# -- CSS --
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "../styles/main.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
load_css()

# -- DATA & MODEL --
@st.cache_data
def load_locations():
    path = os.path.join(os.path.dirname(__file__), "../data/locations.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

LOCATIONS = load_locations()

@st.cache_resource
def get_video_processor():
    return VideoProcessor("best.pt")

vp = get_video_processor()

# -- PRICING LOGIC --
def calculate_parking_charges(hours):
    """
    ₹100 per hour - Real-time calculation
    """
    return int(hours * 100)

# -- STATE --
if 'booking_state' not in st.session_state:
    st.session_state.booking_state = 'select' 
if 'selected_slot' not in st.session_state:
    st.session_state.selected_slot = None
if 'coupon_code' not in st.session_state:
    st.session_state.coupon_code = ""

# -- HEADER --
st.markdown("<h2>Advance Parking Booking</h2>", unsafe_allow_html=True)

# -- LAYOUT --
col_control, col_live = st.columns([1.5, 2])

with col_control:
    st.markdown("### 1. Select Venue")
    
    # 1. Location
    loc_names = list(LOCATIONS.keys())
    display_names = {k: v['name'] for k, v in LOCATIONS.items()}
    
    sel_loc_key = st.selectbox(
        "Choose Location", 
        loc_names, 
        format_func=lambda x: display_names[x]
    )
    
    loc_data = LOCATIONS[sel_loc_key]
    
    # 2. Wing
    wings = list(loc_data.get('wings', {}).keys())
    if len(wings) > 1:
        sel_wing = st.selectbox("Select Wing", wings)
    elif wings:
        sel_wing = wings[0]
        st.caption(f"Section: {sel_wing}")
    else:
        sel_wing = "General"
        
    st.markdown("---")
    
    # 3. Booking Form
    if st.session_state.booking_state == 'select':
        st.info("👈 Check the Live View to find a slot.")
    
    elif st.session_state.booking_state == 'book':
        st.markdown(f"### 2. Book Slot: {st.session_state.selected_slot}")
        
        with st.form("booking_form"):
            st.subheader("💰 Dynamic Pricing")
            start_time = st.time_input("Start Time", value=datetime.now().time())
            duration_hours = st.slider("Duration (hours)", 1, 24, 3)
            
            # Calculate charges LIVE
            charges = calculate_parking_charges(duration_hours)
            
            # End Time Calc
            dt_start = datetime.combine(datetime.today(), start_time)
            dt_end = dt_start + timedelta(hours=duration_hours)
            end_time_str = dt_end.strftime('%I:%M %p')
            
            st.success(f"**Total: ₹{charges}** ({duration_hours}hr × ₹100)")
            st.info(f"**{start_time.strftime('%I:%M %p')} → {end_time_str}**")
            
            if st.form_submit_button(f"✅ BOOK SLOT - Pay ₹{charges}"):
                # Save Booking
                booking_data = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "location": loc_data['name'],
                    "wing": sel_wing,
                    "slot": st.session_state.selected_slot,
                    "start_time": start_time.strftime("%H:%M"),
                    "duration": duration_hours,
                    "amount": charges,
                    "coupon": f"PARK-{st.session_state.selected_slot}-{random.randint(1000,9999)}"
                }
                
                # Append to CSV
                csv_path = os.path.join(os.path.dirname(__file__), "../data/bookings.csv")
                file_exists = os.path.exists(csv_path)
                df = pd.DataFrame([booking_data])
                df.to_csv(csv_path, mode='a', header=not file_exists, index=False)

                st.session_state.booking_state = 'pass'
                st.session_state.coupon_code = booking_data["coupon"]
                st.rerun()

    elif st.session_state.booking_state == 'pass':
        st.success("✅ Payment Successful")
        st.markdown(f"""
        <div style="border: 2px dashed #2ecc71; padding: 20px; border-radius: 10px; text-align: center; background: #f0fff4;">
            <h3 style="color: #27ae60; margin:0;">BOOKING CONFIRMED</h3>
            <h1 style="font-size: 3rem; margin: 10px 0;">{st.session_state.selected_slot}</h1>
            <p><b>{loc_data['name']}</b> | {sel_wing}</p>
            <p style="background: #eee; padding: 5px; border-radius: 5px; font-family: monospace; font-size: 1.2rem;">
                {st.session_state.coupon_code}
            </p>
            <p style="font-size: 0.8rem; color: #888;">Scan this at the entrance gate</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Make Another Booking"):
            st.session_state.booking_state = 'select'
            st.session_state.selected_slot = None
            st.rerun()

# -- RIGHT COLUMN: LIVE VIEW --
with col_live:
    st.markdown(f"### 🔴 LIVE VIEW: {sel_wing}")
    
    # Get Video & JSON
    vid_src = loc_data.get('video_source', 'data/video.mp4')
    if not os.path.exists(vid_src):
        # Fallback for proxy behavior
        vid_src = 'data/video.mp4' 
        
    json_src = loc_data.get('json_source', 'data/video.json')
    
    # Process
    frame, slot_status, free_cnt, occ_cnt = vp.get_live_frame(vid_src, json_src)
    
    # 1. Video Feed
    if frame is not None:
        frame = cv2.resize(frame, (720, 405))
        st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_column_width=True, caption="Live CCTV Feed (YOLOv8 Analysis)")
    else:
        st.error("Live Feed Offline")

    # 2. Grid & Logic
    st.markdown("#### Slot Status")
    
    # Filter slots logic: 
    # If the JSON has IDs like S1, S2... we use them.
    # If JSON is empty, we fake it for demo consistency if needed, but we have real JSON now.
    
    if not slot_status:
        st.warning("No slot configuration found for this view.")
        found_slots = []
    else:
        found_slots = sorted(list(slot_status.keys()), key=lambda x: int(''.join(filter(str.isdigit, x))) if any(c.isdigit() for c in x) else x)

    # Find Nearest
    free_slots = [s for s in found_slots if slot_status[s] == "Free"]
    best_slot = free_slots[0] if free_slots else None
    
    # Grid Display
    cols = st.columns(6)
    for i, slot in enumerate(found_slots):
        status = slot_status[slot]
        color = "#2ecc71" if status == "Free" else "#e74c3c"
        bg_color = "rgba(46, 204, 113, 0.2)" if status == "Free" else "rgba(231, 76, 60, 0.2)"
        border = "2px solid #2ecc71" if status == "Free" else "1px solid #e74c3c"
        
        # Highlight best
        if slot == best_slot:
            border = "3px solid #f1c40f" # Gold for best
            bg_color = "rgba(241, 196, 15, 0.3)"
            
        with cols[i % 6]:
            st.markdown(f"""
            <div style="background: {bg_color}; border: {border}; border-radius: 8px; padding: 10px 5px; text-align: center; margin-bottom: 10px;">
                <strong style="color: {color}; display: block; font-size: 1.1rem;">{slot}</strong>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Action
    if best_slot:
        st.markdown(f"""
        <div style="background: #e8f8f5; padding: 15px; border-radius: 10px; border-left: 5px solid #2ecc71; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 0.9rem; color: #555;">NEAREST AVAILABLE</span>
                <h2 style="margin: 0; color: #27ae60;">{best_slot}</h2>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 1.2rem; display: block;">🟢</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        if st.session_state.booking_state == 'select':
            if st.button(f"BOOK {best_slot} ➔", type="primary"):
                st.session_state.selected_slot = best_slot
                st.session_state.booking_state = 'book'
                st.rerun()
    else:
         st.error("FULL")
