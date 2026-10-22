import streamlit as st, requests, time

URL="http://127.0.0.1:8000/free-slots"
st.title("🚗 Parking Status")

count=st.empty()
slots=st.empty()

while True:
    try:
        r=requests.get(URL).json()
        count.markdown(f"## Free Slots: {r['free_count']}")
        slots.markdown("### "+(", ".join(r["free_slots"]) if r["free_slots"] else "No free slots"))
    except:
        count.error("Backend not reachable")
    time.sleep(1)
