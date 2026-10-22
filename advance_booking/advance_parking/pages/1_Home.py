import streamlit as st

def show_home():
    # Use a container for the main content to center it and apply styling
    with st.container():
        st.markdown("""
        <style>
        .home-title {
            font-size: 3.5rem;
            font-weight: 800;
            color: #1e3a8a;
            text-align: center;
            margin-top: 2rem;
            font-family: 'Helvetica Neue', sans-serif;
        }
        .home-subtitle {
            font-size: 1.5rem;
            color: #64748b;
            text-align: center;
            margin-bottom: 3rem;
            font-family: 'Helvetica Neue', sans-serif;
        }
        .cta-container {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 2rem;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="home-title">Smart Parking System</div>', unsafe_allow_html=True)
        st.markdown('<div class="home-subtitle">Experience seamless, guaranteed parking with live detection.</div>', unsafe_allow_html=True)
        
        # Center the CTA
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style="background-color: white; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); text-align: center; border: 1px solid #e2e8f0;">
                <h3 style="color: #1e293b; margin-bottom: 1rem;">Reserve Your Spot</h3>
                <p style="color: #64748b; margin-bottom: 2rem;">Secure your parking space in advance for Ganesh Glory.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # The button needs to be native Streamlit to handle the page switch
            st.write("")
            if st.button("🚀 Advance Booking", key="adv_booking_home", use_container_width=True):
                st.switch_page("pages/2_Locations.py")

        st.write("")
        st.write("")
        st.markdown("""
        <div style="text-align: center; color: #94a3b8; font-size: 0.9rem;">
            Powered by YOLOv8 Live Detection
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    show_home()
