import streamlit as st
import cv2
import numpy as np
import json
import os
import time
from datetime import datetime, timedelta
from ultralytics import YOLO

# Page Config
st.set_page_config(page_title="User Booking System", page_icon="🚗", layout="wide", initial_sidebar_state="collapsed")

# -- UTILS --
def load_css():
    if os.path.exists("styles/main.css"):
        with open("styles/main.css") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# -- DATA LOADING --
@st.cache_data
def load_locations():
    path = os.path.join("data", "locations.json")
    if not os.path.exists(path):
        st.error(f"Locations file not found at {path}")
        return {}
    with open(path, 'r') as f:
        return json.load(f)

LOCATIONS = load_locations()

# -- YOLO MODEL & VIDEO PROCESSOR --
from backend.video_processor import VideoProcessor

@st.cache_resource
def get_video_processor():
    return VideoProcessor("best.pt")

vp = get_video_processor()

# -- STATE MANAGEMENT --
if 'page_state' not in st.session_state:
    st.session_state.page_state = 'landing' 
if 'booking_step' not in st.session_state:
    st.session_state.booking_step = 1
if 'booking_info' not in st.session_state:
    st.session_state.booking_info = {}

# -- NAVIGATION FUNCTIONS --
def go_to_booking():
    st.session_state.page_state = 'booking'
    st.session_state.booking_step = 1

def go_home():
    st.session_state.page_state = 'landing'

# ==========================================
# VIEW: LANDING PAGE
# ==========================================
if st.session_state.page_state == 'landing':
    st.markdown("<div class='main-header'>", unsafe_allow_html=True)
    st.markdown("<h1 class='hero-title'>Smart Parking Ahmedabad</h1>", unsafe_allow_html=True)
    st.markdown("<p class='hero-subtitle'>Secure your spot at the city's premium venues</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 40px; background: #fff; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h2>Ready to Park?</h2>
            <p style="margin-bottom: 30px;">Book slots for Malls, Riverfront, and Garba Grounds.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.button("ADVANCE BOOK ➔", key="btn_main_adv", on_click=go_to_booking, use_container_width=True)

    st.markdown("<div class='footer'>Smart Parking System © 2026</div>", unsafe_allow_html=True)

# ==========================================
# VIEW: BOOKING FLOW
# ==========================================
elif st.session_state.page_state == 'booking':
    
    # Header
    c_back, c_tit = st.columns([1, 8])
    with c_back:
        st.button("← HOME", on_click=go_home)
    with c_tit:
        st.markdown("<h2>Advance Slot Booking</h2>", unsafe_allow_html=True)

    # STEP 1: SELECT LOCATION
    if st.session_state.booking_step == 1:
        st.markdown("<div class='section-box'>", unsafe_allow_html=True)
        
        loc_names = [f"{k} - {v['name']}" for k, v in LOCATIONS.items()]
        sel_loc_str = st.selectbox("Select Location / Garba Ground", ["-- Select --"] + loc_names)
        
        if sel_loc_str != "-- Select --":
            loc_key = sel_loc_str.split(" - ")[0]
            st.session_state.booking_info['location'] = loc_key
            loc_data = LOCATIONS[loc_key]
            
            st.write("")
            st.markdown(f"**Venue:** {loc_data['name']}")
            
            # DIRECT ACTION: Find best slot
            st.write("")
            if st.button("FIND NEAREST SLOT ➔", type="primary"):
                st.session_state.booking_step = 2
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

    # STEP 2: BEST SLOT RESULT & ACTION
    elif st.session_state.booking_step == 2:
        loc_key = st.session_state.booking_info['location']
        data = LOCATIONS[loc_key]
        
        st.markdown(f"### Scanning: {data['name']}")
        
        # Paths
        video_source = data.get('video_source', 'data/arial2.mp4')
        json_source = data.get('json_source', 'data/arial2.json')

        # Real Processing
        with st.spinner("Analyzing live camera feed (YOLOv8 + PolyIou)..."):
            frame, slot_status, free_cnt, occ_cnt = vp.get_live_frame(video_source, json_source)
        
        col_res, col_act = st.columns([1.5, 1])
        
        with col_res:
            st.markdown("##### Live Analysis")
            if frame is not None:
                # Provide key to force refresh if needed, but stream relies on st.rerun usually
                frame = cv2.resize(frame, (640, 360))
                st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_column_width=True, caption=f"Live Feed: {free_cnt} Free | {occ_cnt} Occupied")
            else:
                 st.error("Video Source Error")
                
        with col_act:
            # Logic: Find Nearest Free
            free_slots = [s for s, status in slot_status.items() if status == "Free"]
            
            if free_slots:
                # Sort numerically if possible (P1, P2...)
                # Heuristic sort: P1, P10, P2 -> P1, P2, P10
                try:
                    free_slots.sort(key=lambda x: int(''.join(filter(str.isdigit, x))))
                except:
                    pass
                
                best_slot = free_slots[0]
                st.session_state.booking_info['slot'] = best_slot
                st.session_state.booking_info['wing'] = "General" 
                
                st.success(f"✅ Slot Available")
                st.markdown(f"""
                <div style="text-align: center; padding: 20px; border: 2px solid #2ecc71; border-radius: 10px; margin-bottom: 20px;">
                    <span style="font-size: 1.2rem; color: #555;">Nearest Slot</span><br>
                    <span style="font-size: 3rem; font-weight: 800; color: #2ecc71;">{best_slot}</span>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"BOOK {best_slot} NOW ➔", type="primary"):
                     st.session_state.booking_step = 3
                     st.rerun()
                     
            else:
                st.error("No Slots Available")
                st.warning("Parking Full")
                if st.button("Try Another Location"):
                    st.session_state.booking_step = 1
                    st.rerun()

    # STEP 3: PAYMENT
    elif st.session_state.booking_step == 3:
        st.markdown("### Payment Details")
        b_info = st.session_state.booking_info
        
        st.info(f"Booking Slot **{b_info['slot']}** at **{LOCATIONS[b_info['location']]['name']}**")
        
        with st.form("pay_form"):
            c1, c2 = st.columns(2)
            start_time = c1.time_input("Arrival Time", value=datetime.now().time())
            duration = c2.slider("Duration (Hours)", 1, 12, 2)
            coupon = st.text_input("Coupon Code")
            
            st.markdown("#### checkout")
            amount = 50 * duration
            st.write(f"Amount: **₹{amount}**")
            
            if st.form_submit_button(f"PAY & CONFIRM"):
                st.session_state.booking_step = 4
                st.rerun()

    # STEP 4: PASS
    elif st.session_state.booking_step == 4:
        st.balloons()
        st.success("Success!")
        b_info = st.session_state.booking_info
        
        st.markdown(f"""
        <div style="background: #f0fdf4; padding: 30px; border: 2px dashed #2ecc71; text-align: center; border-radius: 15px; margin: 20px 0;">
            <h2 style="color: #15803d; margin:0;">ENTRY PASS</h2>
            <p style="color: #666; margin-top:5px;">{LOCATIONS[b_info['location']]['name']}</p>
            <h1 style="font-size: 4rem; margin: 20px 0;">{b_info['slot']}</h1>
            <div style="background: #22c55e; color: white; display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 0.8rem; font-weight: bold;">PAID</div>
            <p style="font-size: 0.8rem; margin-top: 20px; color: #999;">Show this at the gate</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Done"):
            go_home()
            st.rerun()
