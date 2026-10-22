import streamlit as st

st.markdown("# Welcome to Smart Parking")
st.markdown("---")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("""
    ### 🎯 Why Book Advance?
    - ✅ **Guaranteed Slot**
    - 💰 **Best Price** (₹100/hr)
    - 📱 **Digital Coupon** 
    - 🗺️ **Live Availability**
    """)
    
    if st.button("🚀 START BOOKING", use_container_width=True, type="primary"):
        st.session_state.page = 'locations'
        st.rerun()

with col2:
    st.image("https://images.unsplash.com/photo-1558618047-3c8c76fdd7f4?w=600")
    st.caption("Book your parking slot now!")

st.markdown("---")
st.caption("Powered by Real-time Detection")
