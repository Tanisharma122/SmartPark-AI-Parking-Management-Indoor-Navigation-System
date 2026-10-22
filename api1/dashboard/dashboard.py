# dashboard/dashboard.py
import streamlit as st
import requests
from PIL import Image
import os

BACKEND_URL = "http://127.0.0.1:8000"
MASTER_API_KEY = "MASTER-123"

st.set_page_config(page_title="Smart Parking Cameras", layout="wide")
st.title("📹 Smart Parking – Cameras overview")

@st.cache_data(ttl=3)
def fetch_all_cameras():
    resp = requests.get(
        f"{BACKEND_URL}/cameras",
        headers={"X-API-Key": MASTER_API_KEY},
        timeout=5
    )
    resp.raise_for_status()
    return resp.json()

def fetch_camera(camera_id: str):
    resp = requests.get(
        f"{BACKEND_URL}/cameras/{camera_id}",
        headers={"X-API-Key": MASTER_API_KEY},
        timeout=5
    )
    resp.raise_for_status()
    return resp.json()

try:
    data = fetch_all_cameras()
except requests.exceptions.RequestException as e:
    st.error(f"Backend not reachable: {e}")
    st.stop()

cameras = data.get("cameras", [])

st.subheader("All cameras")
if cameras:
    st.table([
        {
            "ID": c["id"],
            "Name": c["name"],
            "Lat": c["lat"],
            "Lng": c["lng"],
            "Floor": c["floor"],
            "Zone": c["zone"],
            "Status": c["status"],
        }
        for c in cameras
    ])

    cam_ids = [c["id"] for c in cameras]
    selected_id = st.selectbox("Select camera", cam_ids)

    if selected_id:
        cam = fetch_camera(selected_id)
        st.subheader(f"Camera: {cam['name']} ({cam['id']})")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total slots", cam["total_slots"])
            st.metric("Free slots", cam["free_slots"])
            st.metric("Occupied slots", cam["occupied_slots"])

        with col2:
            st.write("Geo:")
            st.json({
                "lat": cam["lat"],
                "lng": cam["lng"],
                "floor": cam["floor"],
                "zone": cam["zone"],
            })

        st.subheader("Latest frame (real detection)")
        img_path = os.path.join(
            "C:\\Users\\TANISHA SHARMA\\OneDrive\\Desktop\\parking_management_project\\api\\camera_nodes\\camera1",
            "latest_cam1.jpg",
        )
        if os.path.exists(img_path):
            image = Image.open(img_path)
            st.image(image, caption="Camera 1", use_column_width=True)
        else:
            st.info("Waiting for camera node to save latest frame.")
else:
    st.info("No cameras configured.")
