import streamlit as st
import os

def show_locations():
    st.markdown('<h1 class="main-header">📍 Choose Location</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    # Initialize confirmation state
    if "location_confirmed" not in st.session_state:
        st.session_state.location_confirmed = False

    with col1:
        st.subheader("🔍 Search & Select")
        locations = [
            "Ganesh Glory",
            "Palladium Mall",
            "Alpha Mall",
            "Navratri Parking",
            "Riverfront"
        ]
        
        # If user changes selection, reset confirmation
        selected_loc = st.selectbox("Available Parking Spots", locations, index=0, key="loc_selector")
        
        # Simple Logic: If selection changes, we could reset, but Streamlit re-runs. 
        # We'll use a button to "Confirm"
        
        st.write("---")
        st.write(f"Selection: **{selected_loc}**")
        st.write("📍 Gandhinagar, Gujarat")
        
        if st.button("Confirm Location", use_container_width=True):
            st.session_state.location_confirmed = True
            st.session_state.booking["location"] = {"name": selected_loc}
        
        if st.session_state.location_confirmed and st.session_state.booking.get("location", {}).get("name") == selected_loc:
             st.success("Location Confirmed")
             if selected_loc == "Ganesh Glory":
                if st.button("🚀 VIEW LIVE SLOTS →", type="primary", use_container_width=True):
                    st.switch_page("pages/3_Detection.py")
             else:
                st.warning("⚠️ Live detection offline for this location.")

    with col2:
        st.subheader("📸 Location Preview")
        
        # ONLY show image if confirmed
        if st.session_state.location_confirmed and st.session_state.booking.get("location", {}).get("name") == selected_loc:
            img_path = "static/ganesh_glory.jpg"
            if selected_loc == "Ganesh Glory" and os.path.exists(img_path):
                st.image(img_path, caption=f"Live View: {selected_loc}", use_container_width=True)
            else:
                st.image("https://via.placeholder.com/600x400?text=No+Image+Available", use_container_width=True)
        else:
            # Empty / Placeholder state
            st.info("Please confirm a location to view the live preview.")
            st.markdown("""
            <div style="height: 300px; border: 2px dashed #cbd5e1; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #94a3b8;">
                Preview Hidden
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    show_locations()
