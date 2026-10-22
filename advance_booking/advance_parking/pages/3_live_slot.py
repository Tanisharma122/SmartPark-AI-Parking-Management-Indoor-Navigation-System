import streamlit as st
from detection.detector import ParkingSlotDetector

# Check location
if "location" not in st.session_state.booking:
    st.error("⚠️ Please select a location first!")
    st.stop()

location = st.session_state.booking["location"]
st.markdown(f"# 🅿️ {location['name']} - Live Detection")
st.markdown("---")

# Initialize detector
detector = ParkingSlotDetector()

# REAL DETECTION PATHS (Ganesh Glory)
if location['name'] == "Ganesh Glory":
    image_path = "static/ganesh_glory.jpg"
    json_path = "detection/slots/ganesh_glory.json"
    map_path = "detection/maps/ganesh_glory_map.jpg"
else:
    # Fallback
    image_path = "https://images.unsplash.com/photo-1567808291548-fc3ee04dbcf0?w=700"
    json_path = None

# RUN DETECTION ON CLICK
if st.button("🔍 DETECT FREE SLOTS", type="primary", use_container_width=True):
    with st.spinner("🔄 Analyzing parking lot..."):
        slot_status = detector.detect_slots(image_path, json_path)
        st.session_state.live_slots = slot_status
        st.session_state.detection_image = detector.visualize_detection(image_path, json_path, slot_status)

# Show results if detected
if st.session_state.get('live_slots'):
    slot_status = st.session_state.live_slots
    free_slots = [s for s, status in slot_status.items() if status == "free"]
    
    # 3-COLUMN LAYOUT: Detection Image | Slot Grid | Map
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("### 📸 Live Detection")
        st.image(st.session_state.detection_image, caption="Green=Free, Red=Occupied", use_column_width=True)
    
    with col2:
        st.markdown("### 🟢 Free Slots")
        hours = st.number_input("Hours", min_value=1, max_value=12, value=2)
        total = hours * 100
        st.metric("💰 Total", f"₹{total}")
        
        # SLOT BUTTONS
        cols = st.columns(3)
        for i, slot_id in enumerate(free_slots[:9]):
            with cols[i % 3]:
                if st.button(f"**{slot_id}**\n🟢 FREE", key=f"book_{slot_id}", use_container_width=True):
                    st.session_state.booking.update({
                        "slot_id": slot_id, "hours": hours, "amount": total
                    })
                    st.session_state.page = 'confirm'
                    st.rerun()
    
    with col3:
        st.markdown("### 🗺️ Slot Map")
        if Path(map_path).exists():
            st.image(map_path, caption="Route to your slot", use_column_width=True)
        else:
            st.image("https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=300", 
                    caption="Parking Map")
    
    st.success(f"✅ {len(free_slots)} FREE slots detected!")

# Navigation
col1, col2 = st.columns(2)
with col1:
    if st.button("🔍 Re-scan", use_container_width=True):
        if st.session_state.get('live_slots'):
            del st.session_state.live_slots
        st.rerun()
with col2:
    if st.button("🔙 Back", use_container_width=True):
        st.session_state.page = 'locations'
        st.rerun()

