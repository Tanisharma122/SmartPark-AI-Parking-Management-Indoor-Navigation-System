import streamlit as st
import requests
import time

BACKEND_URL = "http://127.0.0.1:8000/active-free-slots"

st.set_page_config(page_title="Parking Status", layout="centered")
st.title("🚗 Smart Parking Status")

placeholder = st.empty()

while True:
    try:
        data = requests.get(BACKEND_URL, timeout=2).json()

        with placeholder.container():
            st.subheader(f"📷 Active Camera: {data['active_camera']}")
            st.metric("Free Slots", data["free_count"])

            st.write("Camera Status:")
            st.json(data["camera_status"])

            if data["free_slots"]:
                st.success(", ".join(data["free_slots"]))
            else:
                st.warning("No free slots")

    except Exception:
        st.error("Backend not reachable")

    time.sleep(1)
