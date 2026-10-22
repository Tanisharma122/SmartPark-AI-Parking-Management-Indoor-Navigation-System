import streamlit as st
import requests
import cv2
import numpy as np
import os
import time
import socket

# ================= CONFIG =================
def get_backend_url():
    try:
        if "backend" in st.query_params:
            return st.query_params["backend"]
    except: pass
    return "http://127.0.0.1:8000"

BACKEND_URL = get_backend_url()
API_KEY = "sk_org_dashboard_123"
HEADERS = {"x-api-key": API_KEY}

IMAGE_MAP = {
    "arial2.jpg": r"C:\Desktop\parking_management_project\map-Rote-Code\camera_node\camera1\arial2.jpg",
    "vid4.jpg": r"C:\Desktop\parking_management_project\map-Rote-Code\camera_node\camera2\vid4.jpg"
}

# Identify screen mode from modern URL params (Harden against list values)
raw_mode = st.query_params.get("mode", "gate") 
mode = raw_mode[0] if isinstance(raw_mode, list) else str(raw_mode).lower()

st.set_page_config(page_title="SmartWay Navigator", layout="wide", initial_sidebar_state="collapsed")

# UNIVERSAL LUXURY STYLING - ADAPTIVE FOR ALL SCREENS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@500&display=swap');
    
    :root {
        --primary: #00ecff;
        --secondary: #0072ff;
        --bg: #050a15;
        --card: rgba(16, 24, 48, 0.98);
        --text: #ffffff;
    }

    /* Force-Hide Streamlit UI elements that cause white bars */
    [data-testid="stHeader"], [data-testid="stToolbar"], header {
        display: none !important;
    }

    .stApp {
        background: #050a15 !important;
        background: radial-gradient(circle at 50% 10%, #101c3d 0%, #050a15 100%) !important;
        color: var(--text);
    }

    /* Add side spacing for better breathing room */
    .block-container {
        padding: 1rem 1.5rem !important;
        max-width: 1600px !important;
        margin: auto !important;
    }

    /* Fixed Header - Floating Style */
    .smart-header {
        background: rgba(10, 20, 40, 0.95);
        backdrop-filter: blur(30px);
        padding: 1rem 1.8rem;
        border-bottom: 3px solid var(--primary);
        box-shadow: 0 15px 50px rgba(0,0,0,0.6);
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        border-radius: 25px;
        position: relative;
        z-index: 1000;
    }
    
    .logo-font {
        font-weight: 900;
        font-style: italic;
        font-size: 2rem;
        background: linear-gradient(90deg, #00ecff, #0072ff, #00ecff);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 3s linear infinite;
        letter-spacing: -1px;
    }
    
    @keyframes shine {
        to { background-position: 200% center; }
    }

    .status-badge {
        background: linear-gradient(135deg, #00ecff 0%, #0072ff 100%);
        padding: 5px 15px;
        border-radius: 50px;
        font-size: 0.7rem;
        font-weight: 800;
        text-transform: uppercase;
        color: #050a15;
        box-shadow: 0 0 20px rgba(0, 236, 255, 0.5);
    }

    /* Main Content Wrapper */
    .app-main {
        padding: 0 0 2rem 0;
    }

    /* Premium Info Card */
    .info-card {
        background: var(--card);
        border-radius: 30px;
        padding: 2rem;
        border: 1px solid rgba(0, 236, 255, 0.2);
        box-shadow: 0 25px 80px rgba(0,0,0,0.7);
        margin-bottom: 1.5rem;
        text-align: center;
    }

    .slot-id-hero {
        font-size: 5rem;
        font-weight: 900;
        background: linear-gradient(to bottom, #ffffff, #00ecff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1;
        margin: 0.8rem 0;
        filter: drop-shadow(0 0 30px rgba(0, 236, 255, 0.3));
    }

    .stButton > button {
        border-radius: 20px !important;
        padding: 18px !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        border: none !important;
        font-size: 1.1rem !important;
        width: 100% !important;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #00ecff 0%, #0072ff 100%) !important;
        color: #050a15 !important;
        box-shadow: 0 10px 30px rgba(0, 236, 255, 0.4) !important;
    }
    
    .stButton > button:not([kind="primary"]) {
        background: rgba(244, 63, 94, 0.1) !important;
        color: #fb7185 !important;
        border: 1px solid rgba(251, 113, 133, 0.4) !important;
    }

    /* Timer Style */
    .timer {
        font-family: 'JetBrains Mono', monospace;
        font-size: 3rem;
        color: #00ecff;
        margin: 0.5rem 0;
        text-shadow: 0 0 20px rgba(0, 236, 255, 0.4);
    }

    /* Instruction Step Styling */
    .step-box {
        background: rgba(0, 236, 255, 0.08);
        padding: 1rem 1.2rem;
        border-radius: 18px;
        margin-bottom: 0.6rem;
        display: flex;
        align-items: center;
        gap: 15px;
        border: 1px solid rgba(0, 236, 255, 0.2);
        text-align: left;
    }
    
    .step-idx {
        background: var(--primary);
        color: #050a15;
        min-width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 0.8rem;
    }

    /* Map Design */
    .map-frame {
        border-radius: 30px;
        overflow: hidden;
        border: 3px solid rgba(0, 236, 255, 0.15);
        box-shadow: 0 0 100px rgba(0, 236, 255, 0.1);
        margin-bottom: 1.5rem;
    }
    
    /* MOBILE RESPONSIVENESS */
    @media (max-width: 768px) {
        .block-container { padding: 0.5rem 0.8rem !important; }
        .smart-header { padding: 0.8rem 1.2rem; border-radius: 15px; }
        .logo-font { font-size: 1.6rem; }
        .slot-id-hero { font-size: 4rem; }
        .timer { font-size: 2.5rem; }
        .info-card { padding: 1.5rem; border-radius: 20px; }
        .step-box { padding: 0.8rem; font-size: 0.95rem; }
        .map-frame { border-radius: 20px; }
    }
    </style>
""", unsafe_allow_html=True)

# Helper for API calls
def get_api(endpoint):
    try:
        res = requests.get(f"{BACKEND_URL}{endpoint}", headers=HEADERS, timeout=2)
        return res.json() if res.status_code == 200 else None
    except: return None

# State Initialization
for key in ["selected_slot", "reserved_vid", "reservation_confirmed", "reserved_at", "timeout_mins"]:
    if key not in st.session_state: st.session_state[key] = None if key != "reservation_confirmed" else False

# 1. Fetch live data
live_data = get_api("/active-free-slots")
if not live_data:
    st.markdown("<h2 style='text-align:center; padding-top:100px; color:white;'>📡 SYNCING WITH SMARTWAY...</h2>", unsafe_allow_html=True)
    time.sleep(2)
    st.rerun()

active_vid = live_data.get("active_video", "N/A")
display_vid = st.session_state.reserved_vid if st.session_state.reservation_confirmed else active_vid

# Filter available slots
all_slots = live_data.get("slots", [])
available_slots = [s["slot_id"] for s in all_slots if s["video_id"] == display_vid]

# Auto-selection & Conflict Resolution Logic
if not st.session_state.reservation_confirmed:
    # Check if our current previewed slot was stolen by another user
    if st.session_state.selected_slot and st.session_state.selected_slot not in available_slots:
        st.toast(f"📍 Spot {st.session_state.selected_slot} just taken! Recalculating...", icon="🛰️")
        st.session_state.selected_slot = None 

    if available_slots:
        if not st.session_state.selected_slot:
            st.session_state.selected_slot = available_slots[0]
    else:
        st.session_state.selected_slot = None

# HEADER
st.write(f"""
    <div class="smart-header">
        <div class="logo-font">SmartWay</div>
        <div class="status-badge">{'🏡 Pre-Book' if mode=='home' else '🏎️ Gate Access'}</div>
    </div>
""", unsafe_allow_html=True)

# MAIN CONTENT AREA
st.markdown('<div class="app-main">', unsafe_allow_html=True)

# Define column weights for desktop
col_left, col_right = st.columns([1.2, 1.8], gap="large")

with col_left:
    # --- 1. SLOT INFO CARD (TOP STACK) ---
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    if not st.session_state.reservation_confirmed:
        if st.session_state.selected_slot:
            st.markdown(f"<p style='opacity:0.6; margin:0; font-size:1.1rem;'>OPTIMAL SPOT</p><div class='slot-id-hero'>{st.session_state.selected_slot}</div>", unsafe_allow_html=True)
            dur_m = 45 if mode == "home" else 1.5 
            dur_t = "45 MINS" if mode == "home" else "90 SEC"
            if st.button(f"CONFIRM & LOCK", type="primary", use_container_width=True):
                with st.spinner("Locking Spot..."):
                    res = requests.post(f"{BACKEND_URL}/reserve-slot/{display_vid}/{st.session_state.selected_slot}?minutes={float(dur_m)}", headers=HEADERS)
                    if res.status_code == 200 and "error" not in res.json():
                        st.session_state.reservation_confirmed = True
                        st.session_state.reserved_vid = display_vid
                        st.session_state.reserved_at = time.time()
                        st.session_state.timeout_mins = dur_m
                        st.success(f"Slot {st.session_state.selected_slot} locked!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"Failed: {res.json().get('error', 'Unknown Error')}")
                        time.sleep(1)
                        st.rerun()
        else:
            st.markdown("<h3 style='color:#ff4b4b;'>🛑 ALL SPOTS FULL</h3>", unsafe_allow_html=True)
    else:
        # --- THIEF DETECTION & AUTO-REROUTE ---
        # Verification: Is our slot still reserved and NOT occupied?
        slot_check = get_api(f"/check-reservation/{display_vid}/{st.session_state.selected_slot}")
        
        elapsed = int(time.time() - st.session_state.reserved_at)
        total_sec = int(st.session_state.timeout_mins * 60)
        rem = max(0, total_sec - elapsed)

        # If it was stolen (Slot is now occupied but we haven't reached it, or reservation wiped)
        if slot_check and (slot_check.get("status") == "occupied" or not slot_check.get("is_reserved")):
            # Only reroute if we actually still have significant time left (user hasn't arrived)
            if rem > 20 and available_slots:
                new_slot = available_slots[0]
                st.toast(f"🚨 Slot {st.session_state.selected_slot} Taken! Rerouting you to {new_slot}...", icon="🔄")
                # Atomic Re-reservation with REMAINING time
                requests.post(f"{BACKEND_URL}/reserve-slot/{display_vid}/{new_slot}?minutes={rem/60.0}", headers=HEADERS)
                st.session_state.selected_slot = new_slot
                st.rerun()
            elif rem <= 0:
                # Timeout expired - release the reservation
                try:
                    requests.post(f"{BACKEND_URL}/cancel-reservation/{display_vid}/{st.session_state.selected_slot}", headers=HEADERS, timeout=1)
                except:
                    pass  # Silent fail, backend auto-expires anyway
                st.session_state.reservation_confirmed = False
                st.rerun()

        # ACTIVE RESERVATION UI
        st.markdown(f"<h3 style='color:#00ecff; margin:0;'>SECURED: {st.session_state.selected_slot}</h3>", unsafe_allow_html=True)
        st.markdown(f"<div class='timer'>{rem // 60:02d}:{rem % 60:02d}</div>", unsafe_allow_html=True)
        if st.button("CANCEL", use_container_width=True):
            # IMPORTANT: Release the reservation in the database first
            try:
                cancel_res = requests.post(
                    f"{BACKEND_URL}/cancel-reservation/{display_vid}/{st.session_state.selected_slot}",
                    headers=HEADERS,
                    timeout=2
                )
                if cancel_res.status_code == 200:
                    st.toast(f"✅ Slot {st.session_state.selected_slot} released and now available!", icon="🔓")
                else:
                    st.toast("⚠️ Cancellation request sent", icon="📡")
            except:
                st.toast("⚠️ Network issue, but resetting locally", icon="📡")
            
            # Reset session state
            st.session_state.reservation_confirmed = False
            st.session_state.selected_slot = None
            st.session_state.reserved_vid = None
            time.sleep(0.5)  # Brief pause to let backend update
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    # --- 2. THE MAP VIEW (MIDDLE STACK ON MOBILE) ---
    if display_vid != "N/A":
        nav_data = get_api(f"/navigation-data/{display_vid}")
        if nav_data and "error" not in nav_data:
            img_path = IMAGE_MAP.get(nav_data.get("image_name"))
            if img_path and os.path.exists(img_path):
                raw_img = cv2.imread(img_path)
                img = cv2.cvtColor(raw_img, cv2.COLOR_BGR2RGB)
                path_res = get_api(f"/get-path/{display_vid}/{st.session_state.selected_slot}") if st.session_state.selected_slot else None
                if path_res and "path" in path_res:
                    path = path_res["path"]
                    t_xy = tuple(map(int, path[-1]))
                    cv2.circle(img, t_xy, 25, (255,255,255), 5, cv2.LINE_AA)
                    cv2.circle(img, t_xy, 18, (0, 236, 255), -1, cv2.LINE_AA)
                    if st.session_state.reservation_confirmed:
                        overlay = img.copy()
                        for i in range(len(path)-1):
                            p1, p2 = tuple(map(int, path[i])), tuple(map(int, path[i+1]))
                            cv2.line(overlay, p1, p2, (0, 236, 255), 25, cv2.LINE_AA)
                        cv2.addWeighted(overlay, 0.4, img, 0.6, 0, img)
                        for i in range(len(path)-1):
                            p1, p2 = tuple(map(int, path[i])), tuple(map(int, path[i+1]))
                            cv2.line(img, p1, p2, (255, 255, 255), 3, cv2.LINE_AA)
                st.markdown("<div class='map-frame'>", unsafe_allow_html=True)
                st.image(img, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

# --- 3. NAVIGATION GUIDE (BOTTOM STACK ON MOBILE) ---
if st.session_state.reservation_confirmed:
    path_res = get_api(f"/get-path/{display_vid}/{st.session_state.selected_slot}")
    if path_res and "instructions" in path_res:
        st.markdown("<h4 style='margin-bottom:1.2rem; color:#00ecff; font-weight:800; padding: 0 1rem;'>📍 NAVIGATION GUIDE</h4>", unsafe_allow_html=True)
        # Using a single column here to ensure it spans full width below map & info
        for i, step in enumerate(path_res["instructions"]):
            st.markdown(f"""<div style="padding: 0 1rem;"><div class="step-box"><div class="step-idx">{i+1}</div><div style="font-weight:600;">{step}</div></div></div>""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True) 

# Fast Sync
time.sleep(1.0)
st.rerun()
