import streamlit as st
import os
import qrcode
from PIL import Image
import io

st.set_page_config(page_title="Booking Confirmed", page_icon="✅", layout="centered")

# CSS
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "../styles/main.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
load_css()

if 'booking_flow' not in st.session_state or 'coupon' not in st.session_state.booking_flow:
    st.warning("No active booking found.")
    st.stop()
    
flow = st.session_state.booking_flow

st.balloons()
st.title("✅ Booking Confirmed!")

# Pass Card
st.markdown(f"""
<div style="background: white; border: 2px dashed #27ae60; border-radius: 15px; padding: 30px; text-align: center; box-shadow: 0 5px 15px rgba(0,0,0,0.05);">
    <h3 style="color: #27ae60; margin:0;">ENTRY PASS</h3>
    <p style="color: #7f8c8d; margin-top:5px;">{flow['location_name']}</p>
    
    <h1 style="font-size: 3.5rem; color: #2c3e50; margin: 15px 0;">{flow['slot']}</h1>
    
    <div style="display: flex; justify-content: center; gap: 20px; font-size: 0.9rem; color: #555;">
        <span>📅 Today</span>
        <span>🕒 {flow['start_time']}</span>
        <span>⏳ {flow['duration']} hrs</span>
    </div>
    
    <div style="margin: 20px 0; background: #f0fdf4; padding: 10px; border-radius: 8px;">
        <span style="font-family: monospace; font-size: 1.2rem; font-weight: bold; color: #145a32;">{flow['coupon']}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# QR Code
qr = qrcode.make(flow['coupon'])
img_bytes = io.BytesIO()
qr.save(img_bytes, format='PNG')
st.image(img_bytes, caption="Scan at Gate Entry", width=200)

st.write("")
if st.button("Download Pass"):
    st.toast("Pass Downloaded!")

if st.button("🏠 Head Home"):
    st.switch_page("app.py")
