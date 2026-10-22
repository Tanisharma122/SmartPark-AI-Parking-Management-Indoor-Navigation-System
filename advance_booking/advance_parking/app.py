import streamlit as st

# Page config
st.set_page_config(
    page_title="🚗 Smart Parking",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Global Styling
st.markdown("""
<style>
    /* Main Header */
    .main-header {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 3rem;
        font-weight: 700;
        color: #1e3a8a; /* Dark Blue */
        text-align: center;
        margin-bottom: 20px;
    }
    
    /* Sub-header */
    .sub-header {
        font-size: 1.5rem;
        color: #4b5563;
        text-align: center;
        margin-bottom: 40px;
    }

    /* Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: 600;
    }
    
    /* Primary Button (Start Booking) */
    .primary-btn {
        background-color: #2563eb;
        color: white;
    }

    /* Slot Status Colors */
    .free-slot {background-color: #10b981 !important; color: white !important;} /* Green */
    .occupied-slot {background-color: #ef4444 !important; color: white !important;} /* Red */
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #f3f4f6;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'booking' not in st.session_state:
    st.session_state.booking = {
        "location": None,
        "slot_id": None,
        "hours": 1,
        "amount": 0
    }

# Navigation Helper
def main():
    st.sidebar.title("🚗 Navigation")
    
    # We rely on Streamlit's native multipage app behavior for the sidebar mostly,
    # but we can add global controls here if needed.
    
    st.sidebar.info("👋 Welcome to Smart Parking!")
    
    # Current booking status in sidebar
    if st.session_state.booking.get("location"):
        st.sidebar.markdown("---")
        st.sidebar.subheader("📋 Current Booking")
        st.sidebar.write(f"**Loc:** {st.session_state.booking['location']['name']}")
        if st.session_state.booking.get("slot_id"):
             st.sidebar.write(f"**Slot:** {st.session_state.booking['slot_id']}")

if __name__ == "__main__":
    main()
