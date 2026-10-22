import streamlit as st
import os
import sys

# Fix Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.payment import process_payment
from backend.database import add_booking

st.set_page_config(page_title="Secure Payment", page_icon="💳", layout="centered")

# CSS
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "../styles/main.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
load_css()

# Validate Flow
if 'booking_flow' not in st.session_state or not st.session_state.booking_flow:
    st.warning("Session expired.")
    if st.button("Restart"):
        st.switch_page("app.py")
    st.stop()

flow = st.session_state.booking_flow
amount = flow.get('amount', 0)

st.markdown("## 💳 Select Payment Method")
st.info(f"Total Amount to Pay: **₹{amount}**")

# Methods
methods = ["UPI", "Credit/Debit Card", "Net Banking", "Wallet"]
method = st.radio("Choose Method", methods)

st.markdown("---")

if st.button(f"PAY ₹{amount} NOW", type="primary"):
    with st.spinner("Processing Secure Payment..."):
        txn_id = process_payment(amount, method)
    
    if txn_id:
        st.success("Payment Successful!")
        
        # Add extra details
        import random
        coupon_code = f"PARK-{flow['slot']}-{random.randint(1000,9999)}"
        
        # Save to Flow
        st.session_state.booking_flow.update({
            "txn_id": txn_id,
            "coupon": coupon_code,
            "timestamp": "Now" # In DB we use current time
        })
        
        # Save to DB
        from datetime import datetime
        db_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "location": flow['location_name'],
            "wing": flow.get('wing', 'General'),
            "slot": flow['slot'],
            "start_time": flow['start_time'],
            "duration": flow['duration'],
            "amount": amount,
            "coupon": coupon_code
        }
        add_booking(db_data)
        
        st.switch_page("pages/4_success.py")
    else:
        st.error("Payment Failed. Try again.")
