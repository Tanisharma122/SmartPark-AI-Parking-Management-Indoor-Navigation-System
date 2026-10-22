import streamlit as st
import requests
import time

# ================= CONFIG =================
BACKEND_URL = "http://127.0.0.1:8000"
API_KEY = "sk_org_dashboard_123"

PRIMARY_VIDEO = "VID_1"
SECONDARY_VIDEO = "VID_2"

HEADERS = {
    "x-api-key": API_KEY
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
        # Add a timestamp to bypass any browser/network caching
        r = requests.get(
            f"{BACKEND_URL}/active-free-slots?t={time.time()}",
            headers=HEADERS,
            timeout=1
        )
        r.raise_for_status()
        return r.json()
    except:
        return None

# Use a single container to force clean UI updates
main_container = st.empty()

with main_container.container():
    # Main Display Logic
    data = get_active_free_slots()

    if data is None:
        st.error("❌ Backend not reachable. Please check if the API is running.")
    else:
        zones = data.get("zones", [])
        active_vid = data.get("active_video", "N/A")
        
        # Sort zones by video_id to ensure consistent priority (VID_1, VID_2, etc.)
        zones.sort(key=lambda z: z.get("video_id", ""))
        
        all_to_show = []
        seen_slot_ids = set()  # Track unique slots to prevent duplicates
        
        # PRIORITY LOGIC: Show slots from first camera with availability
        # Only move to next camera if current one is completely full
        for zone in zones:
            video_id = zone.get("video_id", "Unknown")
            
            # Collect free slots from THIS camera only (excluding reserved)
            zone_free_slots = []
            for s in zone.get("all_slots", []):
                slot_id = s["slot_id"]
                status = s["status"].upper()
                
                # Skip duplicates
                if slot_id in seen_slot_ids:
                    continue
                
                # Only show genuinely FREE slots (not reserved, not occupied)
                if status == "FREE":
                    seen_slot_ids.add(slot_id)
                    zone_free_slots.append({
                        "id": slot_id, 
                        "status": "FREE", 
                        "color": "#00C851", 
                        "cam": s.get("video_id", video_id)
                    })
            
            # If this camera has free slots, use ONLY these and stop checking other cameras
            if len(zone_free_slots) > 0:
                all_to_show = zone_free_slots
                break  # Don't check remaining cameras
        
        # If no camera had free slots, all_to_show remains empty
        
        all_to_show.sort(key=lambda x: x["id"])

        if len(all_to_show) > 0:
            free_c = data.get("total_free", 0)
            st.markdown(f"### ✅ {free_c} Available Parking Spaces")
            
            # Grid Display
            cols = st.columns(4)
            for i, slot in enumerate(all_to_show):
                with cols[i % 4]:
                    st.markdown(f"""
                        <div class="slot-box" style="background-color: {slot['color']};">
                            <p class="slot-label">{slot['status']}</p>
                            <p class="slot-id">{slot['id']}</p>
                            <p class="cam-label">{slot['cam']}</p>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("### 🚫 ALL SPACES FULL")
            st.info(f"Monitoring sensors for departures...")

# ---------- AUTO REFRESH LOOP ----------
time.sleep(REFRESH_INTERVAL)
st.rerun()
