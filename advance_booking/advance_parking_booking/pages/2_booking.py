import streamlit as st
import os
import sys
from datetime import datetime, timedelta

# Fix Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.pricing import calculate_parking_charges

st.set_page_config(page_title="Booking Details", page_icon="📝", layout="centered")

# CSS
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "../styles/main.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
load_css()

# Validate Flow
if 'booking_flow' not in st.session_state or not st.session_state.booking_flow:
    st.warning("Please select a location first.")
    if st.button("Go to Location Select"):
        st.switch_page("pages/1_location.py")
    st.stop()

flow = st.session_state.booking_flow

st.markdown(f"## 📝 Booking Details")

# Card Display or Info
st.markdown(f"""
<div style="background: #eaf2f8; padding: 20px; border-radius: 10px; border-left: 5px solid #3498db; margin-bottom: 20px;">
    <h3 style="margin:0; color: #2c3e50;">BOOKING SLOT: {flow['slot']}</h3>
    <p style="margin:5px 0 0 0; color: #555;">{flow['location_name']} | {flow.get('wing','General')}</p>
</div>
""", unsafe_allow_html=True)

with st.form("booking_form"):
    c1, c2 = st.columns(2)
    start_time = c1.time_input("Start Time", value=datetime.now().time())
    duration = c2.slider("Duration (Hours)", 1, 24, 3)
    
    # Live Calc
    charges = calculate_parking_charges(duration)
    
    # End Time
    dt_now = datetime.now()
    dt_start = datetime.combine(dt_now.date(), start_time)
    dt_end = dt_start + timedelta(hours=duration)
    
    st.markdown("---")
    st.subheader(f"Total: ₹{charges}")
    st.caption(f"Valid until: {dt_end.strftime('%I:%M %p')}")
    
    if st.form_submit_button("CONFIRM & PAY ➔", type="primary"):
        # Update State
        st.session_state.booking_flow.update({
            "start_time": start_time.strftime("%H:%M"),
            "duration": duration,
            "end_time": dt_end.strftime("%H:%M"),
            "amount": charges
        })
        st.switch_page("pages/3_payment.py")
