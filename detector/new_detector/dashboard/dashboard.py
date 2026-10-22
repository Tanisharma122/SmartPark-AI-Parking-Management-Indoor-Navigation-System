import streamlit as st
import requests
import time

BACKEND_BASE = "http://127.0.0.1:8000"  # or your LAN IP, e.g. http://192.168.1.23:8000
BACKEND_URL = f"{BACKEND_BASE}/free-slots"
RECO_URL    = f"{BACKEND_BASE}/recommendation"


st.set_page_config(page_title="Parking Status", layout="wide")
st.title("🚗 Parking Status (Image-based)")

placeholder = st.empty()

while True:
    try:
        data = requests.get(BACKEND_URL, timeout=2).json()
        reco = requests.get(RECO_URL, timeout=2).json()

        with placeholder.container():
            st.markdown("### Cameras overview")

            cols = st.columns(len(data)) if data else []
            for col, (cam_id, info) in zip(cols, data.items()):
                with col:
                    st.subheader(f"📷 {cam_id}")
                    st.metric("Total slots", info["total"])
                    st.metric("Free", len(info["free"]))
                    st.metric("Occupied", len(info["occupied"]))
                    st.write("**Free slots:** " + (", ".join(info["free"]) or "None"))

            st.markdown("---")
            st.markdown("### Recommendation (if cam1 full → cam2)")
            if reco["camera"]:
                st.success(
                    f"Use **{reco['camera']}**. "
                    f"Free slots: {', '.join(reco['free_slots'])}"
                )
            else:
                st.error("No free slots in any camera")

    except Exception:
        st.error("Backend not reachable")

    time.sleep(2)
