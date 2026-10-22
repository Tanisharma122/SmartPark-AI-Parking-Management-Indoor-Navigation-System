import streamlit as st
import requests
import time

# ================= CONFIG =================
BACKEND_URL = "http://127.0.0.1:8000"
API_KEY = "sp_live_3fa85f64a12b9d9a8e5f3c2b1a0d4e6f"

PRIMARY_CAMERA = "CAM_1"
SECONDARY_CAMERA = "CAM_2"

HEADERS = {
    "X-API-KEY": API_KEY
}

REFRESH_INTERVAL = 0.5 
# =========================================

st.set_page_config(
    page_title="Smart Parking Status",
    layout="wide"
)

# Custom CSS for big slot numbers
st.markdown("""
    <style>
    .slot-box {
        background-color: #00C851;
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        min-height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .slot-id {
        font-size: 50px !important;
        font-weight: bold;
        margin: 0;
    }
    .slot-label {
        font-size: 14px;
        opacity: 0.8;
        margin-bottom: -5px;
    }
    .cam-label {
        font-size: 12px;
        opacity: 0.6;
        margin-top: 5px;
    }
    .stApp {
        background-color: #f0f2f6;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚗 LED Dashboard: Parking Availability")

def get_active_free_slots():
    try:
        r = requests.get(
            f"{BACKEND_URL}/active-free-slots",
            headers=HEADERS,
            timeout=1
        )
        r.raise_for_status()
        return r.json()
    except:
        return None

# Use a placeholder to keep the UI from flickering
placeholder = st.empty()

with placeholder.container():
    data = get_active_free_slots()

    if data is None:
        st.error("❌ Backend not reachable. Please check if the API is running.")
    else:
        slots = data["slots"]
        
        if len(slots) > 0:
            current_cam = slots[0]["camera_id"]
            if current_cam == PRIMARY_CAMERA:
                st.success(f"✅ {PRIMARY_CAMERA} Active | {len(slots)} Spaces Found")
            else:
                st.warning(f"⚠ {PRIMARY_CAMERA} Full | Showing {SECONDARY_CAMERA} ({len(slots)} Spaces)")
            
            # Grid Display
            cols = st.columns(4)
            for i, slot in enumerate(slots):
                with cols[i % 4]:
                    st.markdown(f"""
                        <div class="slot-box">
                            <p class="slot-label">SLOT</p>
                            <p class="slot-id">{slot['slot_id']}</p>
                            <p class="cam-label">{slot['camera_id']}</p>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.error("🚫 ALL SPACES FULL. Please wait for a vehicle to leave.")

# ---------- AUTO REFRESH LOOP ----------
time.sleep(REFRESH_INTERVAL)
st.rerun()
