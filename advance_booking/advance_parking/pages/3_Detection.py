import streamlit as st
import os
from detection.detector import ParkingSlotDetector

# Initialize detector (cached to avoid reloading model)
@st.cache_resource
def get_detector():
    return ParkingSlotDetector("models/best.pt")

def show_detection():
    st.markdown('<h1 class="main-header">🅿️ Live Slot Detection</h1>', unsafe_allow_html=True)

    # Check context
    if not st.session_state.booking.get("location"):
        st.warning("Please select a location first.")
        if st.button("← Go Back"):
            st.switch_page("pages/2_Locations.py")
        return

    location_name = st.session_state.booking["location"]["name"]
    
    # Explicitly mapping to the requested JSON file
    if location_name == "Ganesh Glory":
        img_path = "static/ganesh_glory.jpg"
        # USES REAL JSON DATA AS REQUESTED
        json_path = "detection/slots/ganesh_glory.json"
        display_name = "Ganesh Glory"
    else:
        st.error(f"Configuration for {location_name} not found.")
        return

    # Layout
    col1, col2 = st.columns([2, 1])
    
    detector = get_detector()
    
    # State for detection results
    if 'slot_status' not in st.session_state:
        st.session_state.slot_status = {}

    with col1:
        st.subheader(f"📸 Live Feed: {display_name}")
        
        # Action Button to detect
        if st.button("🔍 DETECT FREE SLOTS →", type="primary", use_container_width=True):
            with st.spinner("Analyzing camera feed..."):
                # Detects using the real JSON coordinates
                status = detector.detect_slots(img_path, json_path)
                st.session_state.slot_status = status
        
        # visualizer
        if st.session_state.slot_status:
            viz_img = detector.visualize_detection(img_path, json_path, st.session_state.slot_status)
            st.image(viz_img, caption="Green = Free, Red = Occupied", use_container_width=True)
        else:
            if os.path.exists(img_path):
                st.image(img_path, caption="Raw Feed", use_container_width=True)
            else:
                st.error("Feed image not found.")

    with col2:
         st.subheader("🟢 Availability")
         
         if not st.session_state.slot_status:
             st.info("Click 'DETECT' to see available slots.")
         else:
             free_slots = [k for k, v in st.session_state.slot_status.items() if v == "free"]
             
             st.metric("Free Slots", len(free_slots))
             
             if not free_slots:
                 st.error("No slots available currently!")
             else:
                 st.markdown("### Select a Free Slot:")
                 # Display as a clean list/grid of buttons
                 for slot in sorted(free_slots):
                     if st.button(f"Slot {slot} ➡️", key=f"btn_{slot}", use_container_width=True):
                         st.session_state.booking["slot_id"] = slot
                         st.switch_page("pages/4_Confirm.py")

    st.write("---")
    if st.button("⬅️ Change Location"):
        st.switch_page("pages/2_Locations.py")

if __name__ == "__main__":
    show_detection()
