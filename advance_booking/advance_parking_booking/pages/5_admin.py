import streamlit as st
import pandas as pd
import os
import sys
import json

# Fix Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.database import get_all_bookings
from backend.detection import VideoProcessor

st.set_page_config(page_title="Admin Console", page_icon="⚙️", layout="wide")

# CSS
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "../styles/main.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
load_css()

# Data
@st.cache_data
def load_locations():
    path = os.path.join(os.path.dirname(__file__), "../data/locations.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

LOCATIONS = load_locations()

@st.cache_resource
def get_vp():
    return VideoProcessor("best.pt")
vp = get_vp()

st.title("⚙️ Admin Dashboard")
tab1, tab2 = st.tabs(["📊 Live Occupancy", "💰 Revenue & Bookings"])

# TAB 1: Live Occupancy
with tab1:
    st.subheader("Live Slot Monitoring")
    
    if st.button("Refresh Live Stats"):
        st.cache_data.clear()
        st.rerun()
        
    stats_data = []
    total_cap = 0
    total_occ = 0
    
    # Grid View for Locations
    cols = st.columns(3)
    
    for i, (key, data) in enumerate(LOCATIONS.items()):
        vid = data.get('video_source', '')
        js = data.get('json_source', '')
        
        # Run Inference
        if os.path.exists(vid):
            _, _, free, occ = vp.get_live_frame(vid, js)
        else:
            free, occ = 10, 0
            
        full_slots = free + occ
        total_cap += full_slots
        total_occ += occ
        
        occ_pct = (occ / full_slots) * 100 if full_slots > 0 else 0
        
        # Append to detailed stats
        stats_data.append({
            "Location": data['name'],
            "Capacity": full_slots,
            "Free": free,
            "Occupied": occ,
            "Occupancy %": f"{occ_pct:.1f}%"
        })
        
        # Mini Card in Grid
        stat_color = "red" if occ_pct > 80 else "green"
        with cols[i % 3]:
            st.markdown(f"""
            <div style="border:1px solid #ddd; padding:15px; border-radius:10px; margin-bottom:10px; background:white;">
                <h4 style="margin:0;">{data['name']}</h4>
                <div style="display:flex; justify-content:space-between; margin-top:10px;">
                    <span style="color:#27ae60;">🟢 {free} Free</span>
                    <span style="color:#c0392b;">🔴 {occ} Busy</span>
                </div>
                <div style="background:#eee; height:5px; width:100%; margin-top:5px; border-radius:3px;">
                    <div style="background:{stat_color}; width:{occ_pct}%; height:100%; border-radius:3px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("---")
    st.dataframe(pd.DataFrame(stats_data), use_container_width=True)


# TAB 2: Revenue
with tab2:
    st.subheader("Booking Ledger (SQLite)")
    
    df = get_all_bookings()
    
    if not df.empty:
        # Metrics
        rev = df['amount'].sum()
        count = len(df)
        
        m1, m2 = st.columns(2)
        m1.metric("Total Bookings", count)
        m2.metric("Total Revenue", f"₹{rev}")
        
        st.dataframe(
            df,
            column_config={
                "timestamp": "Time",
                "amount": st.column_config.NumberColumn("Amount", format="₹%d"),
                "status": st.column_config.BadgeColumn("Status", map_labels={"CONFIRMED": "#2ecc71"})
            },
            use_container_width=True
        )
    else:
        st.info("No bookings found in database.")
