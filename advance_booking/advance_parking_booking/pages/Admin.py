import streamlit as st
import pandas as pd
import os
import sys

# -- PATH FIX --
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import random

# -- SETUP --
st.set_page_config(page_title="Admin Dashboard", page_icon="📊", layout="wide")

# -- UTILS --
def load_css():
    if os.path.exists("styles/main.css"):
        with open("styles/main.css") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# -- DATA LOADING --
@st.cache_data
def load_locations():
    path = os.path.join("data", "locations.json")
    if not os.path.exists(path):
         st.error(f"Locations file not found at {path}")
         return {}
    with open(path, 'r') as f:
        return json.load(f)

LOCATIONS = load_locations()

# -- VIDEO PROCESSOR --
from backend.video_processor import VideoProcessor

@st.cache_resource
def get_video_processor():
    return VideoProcessor("best.pt")

vp = get_video_processor()

# -- HEADER --
st.markdown("<div class='main-header'>", unsafe_allow_html=True)
st.markdown("<h2>Admin Dashboard - Live Monitoring</h2>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# -- OVERALL STATS --
total_capacity = 0
total_occupied = 0
stats_data = []

# Logic to calculate stats (REAL)
for loc_key, loc_data in LOCATIONS.items():
    loc_name = loc_data['name']
    
    # Process
    vid_src = loc_data.get('video_source', '')
    json_src = loc_data.get('json_source', '')
    
    # We only process if we have valid sources
    if os.path.exists(vid_src):
        # Run inference for stats
        _, _, free, occupied = vp.get_live_frame(vid_src, json_src)
        
        n_slots = free + occupied
        if n_slots == 0: 
             # Fallback if no JSON loaded or empty
             n_slots = 10 
             free = 10
             occupied = 0
        
        total_capacity += n_slots
        total_occupied += occupied
        
        stats_data.append({
            "Location": loc_name,
            "Total Slots": n_slots,
            "Free (Green)": free,
            "Occupied (Red)": occupied
        })

total_free = total_capacity - total_occupied

# KPIS
c1, c2, c3 = st.columns(3)
c1.metric("Total System Capacity", total_capacity)
c2.metric("Available Slots", total_free, delta_color="normal")
c3.metric("Occupied Slots", total_occupied, delta_color="inverse")

st.markdown("---")

# -- DETAILED TABLE --
st.markdown("### Real-Time Occupancy")

df = pd.DataFrame(stats_data)

st.dataframe(
    df,
    column_config={
        "Free (Green)": st.column_config.ProgressColumn(
            "Free Slots",
            help="Available slots",
            format="%d",
            min_value=0,
            max_value=32, # Max seen in JSON is around 32
        ),
        "Occupied (Red)": st.column_config.NumberColumn(
            "Occupied",
            help="Occupied slots",
        )
    },
    use_container_width=True,
    hide_index=True
)

st.markdown("---")
if st.button("Refresh Live Data"):
    st.cache_data.clear()
    st.rerun()

# -- BOOKING LEDGER --
st.markdown("### 📋 User Booking Ledger")
csv_path = "data/bookings.csv"

if os.path.exists(csv_path):
    # Load Bookings
    bookings_df = pd.read_csv(csv_path)
    # Sort by recent
    bookings_df = bookings_df.sort_values(by="timestamp", ascending=False)
    
    st.dataframe(
        bookings_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "timestamp": "Time",
            "amount": st.column_config.NumberColumn("Amount (₹)", format="₹%d"),
            "coupon": "Ticket ID"
        }
    )
    
    # Revenue Stats
    total_rev = bookings_df['amount'].sum()
    st.metric("Total Revenue", f"₹{total_rev}")
    
else:
    st.info("No bookings recorded yet.")

st.markdown("<div class='footer'>Admin Console</div>", unsafe_allow_html=True)
