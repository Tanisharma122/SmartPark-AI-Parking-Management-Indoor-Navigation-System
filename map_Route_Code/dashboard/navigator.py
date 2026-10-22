import streamlit as st
import requests
import cv2
import numpy as np
import os
import time

# ================= CONFIG =================
BACKEND_URL = "http://127.0.0.1:8000"
API_KEY = "sp_live_3fa85f64a12b9d9a8e5f3c2b1a0d4e6f"
HEADERS = {"X-API-KEY": API_KEY}

# Dynamic path resolution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAM_NODE_DIR = os.path.join(BASE_DIR, "camera_node")

# Mapping to live frames or fallback static images
IMAGE_MAP = {
    "arial2.jpg": {
        "live": os.path.join(CAM_NODE_DIR, "camera1", "live.jpg"),
        "static": os.path.join(CAM_NODE_DIR, "camera1", "arial2.jpg")
    },
    "vid4.jpg": {
        "live": os.path.join(CAM_NODE_DIR, "camera2", "live.jpg"),
        "static": os.path.join(CAM_NODE_DIR, "camera2", "vid4.jpg")
    }
}

PRIMARY_CAMERA = "CAM_1"
SECONDARY_CAMERA = "CAM_2"
REFRESH_INTERVAL = 0.5 

# Colors (BGR for OpenCV, Hex for CSS)
COLOR_ROUTE = (255, 60, 0)      # Neon Blue
COLOR_ENTRY = (0, 255, 100)      # Bright Green
COLOR_TARGET = (50, 50, 255)     # Soft Red
# =========================================

st.set_page_config(page_title="Parking Navigator", layout="wide")

# Premium CSS Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-title {
        font-weight: 800;
        font-size: 2.5rem;
        color: #1e293b;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    
    .stButton > button {
        border-radius: 12px;
        border: none;
        padding: 0.75rem 1rem;
        font-weight: 600;
        transition: all 0.2s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .instruction-card {
        background: #ffffff;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        border: 1px solid #f1f5f9;
        margin-top: 20px;
    }
    
    .instruction-header {
        color: #334155;
        font-weight: 700;
        font-size: 1.25rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .instruction-step {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 12px;
        color: #64748b;
        font-size: 1rem;
        line-height: 1.6;
    }
    
    .step-icon {
        background: #eff6ff;
        color: #3b82f6;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 0.8rem;
        flex-shrink: 0;
    }
    
    .map-container {
        border-radius: 24px;
        overflow: hidden;
        box-shadow: 0 20px 50px rgba(0,0,0,0.1);
        border: 4px solid #ffffff;
    }
    
    .status-badge {
        padding: 6px 12px;
        border-radius: 99px;
        font-size: 0.75rem;
        font-weight: 700;
        background: #f1f5f9;
        color: #475569;
        margin-bottom: 1rem;
        display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">📍 Smart Wayfinder</h1>', unsafe_allow_html=True)

# ---------- HELPERS ----------
def get_api(endpoint):
    try:
        r = requests.get(f"{BACKEND_URL}{endpoint}", headers=HEADERS, timeout=1)
        return r.json() if r.status_code == 200 else None
    except: return None

def draw_luxury_path(img, path, color=(255, 60, 0)):
    # Create an overlay for glow
    overlay = img.copy()
    
    # 1. Draw glowing background line
    for i in range(len(path)-1):
        p1, p2 = tuple(map(int, path[i])), tuple(map(int, path[i+1]))
        cv2.line(overlay, p1, p2, color, 12, cv2.LINE_AA)
    
    # Apply slightly transparent overlay
    cv2.addWeighted(overlay, 0.3, img, 0.7, 0, img)
    
    # 2. Draw sharp center line
    for i in range(len(path)-1):
        p1, p2 = tuple(map(int, path[i])), tuple(map(int, path[i+1]))
        cv2.line(img, p1, p2, color, 4, cv2.LINE_AA)
        
        # Draw small elegant directional markers (arrows)
        if i % 3 == 0:
            mid = ((p1[0]+p2[0])//2, (p1[1]+p2[1])//2)
            # Calculate direction vector
            dx, dy = p2[0]-p1[0], p2[1]-p1[1]
            dist = np.sqrt(dx**2 + dy**2)
            if dist > 0:
                ux, uy = dx/dist, dy/dist
                # Draw a clean arrow tip
                tp1 = (int(mid[0] - 10*ux + 6*uy), int(mid[1] - 10*uy - 6*ux))
                tp2 = (int(mid[0] - 10*ux - 6*uy), int(mid[1] - 10*uy + 6*ux))
                cv2.line(img, (int(mid[0]), int(mid[1])), tp1, color, 2, cv2.LINE_AA)
                cv2.line(img, (int(mid[0]), int(mid[1])), tp2, color, 2, cv2.LINE_AA)

# ---------- LOGIC ----------
if "selected_slot" not in st.session_state:
    st.session_state.selected_slot = None

# Get active slots first to determine which camera is currently in focus
live_data = get_api("/active-free-slots")

if live_data:
    slots = live_data.get("slots", [])
    active_cam = slots[0]["camera_id"] if slots else "OFFLINE"
    display_list = [s["slot_id"] for s in slots]

    # Get navigation data for the active camera
    nav_data = get_api(f"/navigation-data/{active_cam}")

    if nav_data and "error" not in nav_data:
        # Reset selection if slot becomes unavailable
        if st.session_state.selected_slot and st.session_state.selected_slot not in display_list:
            st.session_state.selected_slot = None

        col1, col2 = st.columns([1, 4], gap="large")

        with col1:
            st.markdown(f'<div class="status-badge">CAMERA: {active_cam}</div>', unsafe_allow_html=True)
            st.subheader("Available Spaces")
            
            if not display_list:
                st.warning("Parking Full")
            else:
                for sid in display_list:
                    is_sel = (st.session_state.selected_slot == sid)
                    if st.button(sid, key=f"btn_{sid}", type="primary" if is_sel else "secondary"):
                        st.session_state.selected_slot = sid
                        st.rerun()

        with col2:
            img_name = nav_data.get("image_name")
            img_config = IMAGE_MAP.get(img_name)
            img_path = None
            
            if img_config:
                # Try live frame first, then static
                if os.path.exists(img_config["live"]):
                    img_path = img_config["live"]
                elif os.path.exists(img_config["static"]):
                    img_path = img_config["static"]
            
            if img_path and os.path.exists(img_path):
                # Use a unique key to prevent caching of the live image in Streamlit
                raw_img = cv2.imread(img_path)
                img = cv2.cvtColor(raw_img, cv2.COLOR_BGR2RGB)
                instructions = []

                if st.session_state.selected_slot:
                    path_res = get_api(f"/get-path/{active_cam}/{st.session_state.selected_slot}")
                    if path_res and "path" in path_res:
                        draw_luxury_path(img, path_res["path"], color=COLOR_ROUTE)
                        instructions = path_res.get("instructions", [])
                        
                        # Entry Node with styling
                        entry_xy = tuple(map(int, nav_data["lanes"]["entry"]))
                        cv2.circle(img, entry_xy, 18, (255, 255, 255), -1, cv2.LINE_AA)
                        cv2.circle(img, entry_xy, 12, COLOR_ENTRY, -1, cv2.LINE_AA)
                        cv2.putText(img, "ENTRY", (entry_xy[0]-35, entry_xy[1]-30), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 3, cv2.LINE_AA)
                        cv2.putText(img, "ENTRY", (entry_xy[0]-35, entry_xy[1]-30), cv2.FONT_HERSHEY_DUPLEX, 0.7, COLOR_ENTRY, 1, cv2.LINE_AA)

                        # Target Node with styling
                        target_xy = tuple(map(int, path_res["path"][-1]))
                        cv2.circle(img, target_xy, 18, (255, 255, 255), -1, cv2.LINE_AA)
                        cv2.circle(img, target_xy, 12, COLOR_TARGET, -1, cv2.LINE_AA)
                        label = f"SLOT {st.session_state.selected_slot}"
                        cv2.putText(img, label, (target_xy[0]-45, target_xy[1]-35), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 3, cv2.LINE_AA)
                        cv2.putText(img, label, (target_xy[0]-45, target_xy[1]-35), cv2.FONT_HERSHEY_DUPLEX, 0.8, COLOR_TARGET, 1, cv2.LINE_AA)

                st.markdown('<div class="map-container">', unsafe_allow_html=True)
                st.image(img, use_column_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

                if instructions:
                    st.markdown('<div class="instruction-card"><div class="instruction-header">🗺️ Route Instructions</div>', unsafe_allow_html=True)
                    for i, step in enumerate(instructions):
                        st.markdown(f"""
                            <div class="instruction-step">
                                <div class="step-icon">{i+1}</div>
                                <div>{step}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info(f"Interactive navigation for {active_cam} is initializing...")
        
    else:
        st.error(f"Waiting for synchronization with {active_cam}...")

else:
    st.error("Connecting to server...")

time.sleep(REFRESH_INTERVAL)
st.rerun()
