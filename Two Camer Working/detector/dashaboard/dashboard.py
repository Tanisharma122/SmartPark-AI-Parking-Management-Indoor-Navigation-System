# import streamlit as st, requests, time

# URL="http://127.0.0.1:8000/free-slots"
# st.title("🚗 Parking Status")

# count=st.empty()
# slots=st.empty()

# while True:
#     try:
#         r=requests.get(URL).json()
#         count.markdown(f"## Free Slots: {r['free_count']}")
#         slots.markdown("### "+(", ".join(r["free_slots"]) if r["free_slots"] else "No free slots"))
#     except:
#         count.error("Backend not reachable")
#     time.sleep(1)

import streamlit as st
import requests
import time

BACKEND_URL = "http://127.0.0.1:8000/free-slots"

st.set_page_config(page_title="Parking Status", layout="wide")
st.title("🚗 Parking Status")

placeholder = st.empty()

while True:
    try:
        data = requests.get(BACKEND_URL, timeout=2).json()

        with placeholder.container():
            cols = st.columns(len(data)) if data else []

            for col, (camera_id, slots) in zip(cols, data.items()):
                with col:
                    st.subheader(f"📷 {camera_id}")
                    st.metric("Free Slots", len(slots))

                    if slots:
                        st.write(", ".join(slots))
                    else:
                        st.write("No free slots")

    except Exception as e:
        st.error("Backend not reachable")

    time.sleep(1)
