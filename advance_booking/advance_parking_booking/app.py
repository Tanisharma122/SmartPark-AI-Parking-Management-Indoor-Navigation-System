import streamlit as st
import os

# -- PAGE CONFIG --
st.set_page_config(page_title="Advance Parking System", layout="wide", page_icon="🚗")

# -- CSS --
def load_css():
    if os.path.exists("styles/main.css"):
        with open("styles/main.css") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
load_css()

# -- HEADER --
st.markdown("<div class='main-header'>", unsafe_allow_html=True)
st.markdown("<h1 class='hero-title'>🚗 ADVANCE PARKING BOOKING SYSTEM</h1>", unsafe_allow_html=True)
st.markdown("<p class='hero-subtitle'>Ahmedabad Malls & Garba Plots</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# -- MAIN AREA --
st.write("")
st.write("")
c1, c2, c3 = st.columns([1, 2, 1])

with c2:
    st.markdown("""
    <div style="text-align: center; padding: 40px; background: white; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
        <h2 style="color:#2c3e50; margin-bottom:20px;">Secure Your Spot Instantly</h2>
        <p style="color:#7f8c8d; font-size:1.1rem; margin-bottom:40px;">
            Live availability tracking, dynamic pricing, and seamless entry.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Custom CSS class for green button if needed, but primary is fine
    if st.button("🎯 ADVANCE BOOK NOW", type="primary", use_container_width=True):
        st.switch_page("pages/1_location.py")

st.markdown("<div class='footer'>Ahmedabad Municipal Smart Parking Initiative © 2026</div>", unsafe_allow_html=True)
