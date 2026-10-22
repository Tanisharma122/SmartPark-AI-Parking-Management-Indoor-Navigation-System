import streamlit as st
import json
import random
import datetime
from datetime import timedelta

def save_booking(booking_data):
    file_path = "data/bookings.json"
    try:
        with open(file_path, 'r') as f:
            bookings = json.load(f)
    except:
        bookings = []
    
    bookings.append(booking_data)
    
    with open(file_path, 'w') as f:
        json.dump(bookings, f, indent=4)

def update_exit_time():
    # Callback to auto-update exit time to 2 hours after entry
    if "booking_entry" in st.session_state:
        et = st.session_state.booking_entry
        # Combine with today to do math
        dt = datetime.datetime.combine(datetime.date.today(), et)
        dt_exit = dt + timedelta(hours=2)
        st.session_state.booking_exit = dt_exit.time()

def show_confirm():
    st.markdown('<h1 class="main-header">✅ Complete Booking</h1>', unsafe_allow_html=True)

    # Check context
    if not st.session_state.booking.get("slot_id"):
        st.warning("No slot selected.")
        if st.button("← Go to Detection"):
             st.switch_page("pages/3_Detection.py")
        return

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📝 Booking Details")
        
        loc = st.session_state.booking["location"]["name"]
        slot = st.session_state.booking["slot_id"]
        
        st.info(f"📍 **Location:** {loc}")
        st.info(f"🅿️ **Slot:** {slot}")
        
        st.write("---")
        st.write("#### ⏰ Select Timing")
        
        # Initialize defaults in session state if not set
        if "booking_entry" not in st.session_state:
            now = datetime.datetime.now()
            default_entry = (now + timedelta(minutes=15 - now.minute % 15)).time()
            st.session_state.booking_entry = default_entry
            
            # Default exit 2 hours later
            dt_exit = datetime.datetime.combine(datetime.date.today(), default_entry) + timedelta(hours=2)
            st.session_state.booking_exit = dt_exit.time()

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            # Entry Time with callback
            entry_time = st.time_input(
                "Entry Time", 
                key="booking_entry",
                on_change=update_exit_time
            )
        with col_t2:
            # Exit Time
            exit_time = st.time_input(
                "Exit Time", 
                key="booking_exit"
            )
            
        # Calc Duration
        t1 = datetime.datetime.combine(datetime.date.today(), entry_time)
        t2 = datetime.datetime.combine(datetime.date.today(), exit_time)
        
        # Handle overnight
        if t2 < t1:
            t2 += timedelta(days=1)
            
        duration = t2 - t1
        hours = duration.total_seconds() / 3600
        
        # Display logic
        if hours <= 0:
             st.error("Invalid time selection.")
             amount = 0
             valid_time = False
        else:
             valid_time = True
             hours =  round(hours, 2)
             amount = int(hours * 100)
             
             # Store in booking dict
             st.session_state.booking["entry_time"] = str(entry_time)
             st.session_state.booking["exit_time"] = str(exit_time)
             st.session_state.booking["hours"] = hours
             st.session_state.booking["amount"] = amount
             
             # Big Metric Display
             st.markdown(f"""
             <div style="background-color: #eff6ff; padding: 15px; border-radius: 10px; border: 1px solid #bfdbfe; text-align: center;">
                <span style="font-size: 1.2rem; color: #64748b;">Total Pay (₹100/hr)</span><br>
                <span style="font-size: 2.5rem; font-weight: bold; color: #2563eb;">₹{amount}</span><br>
                <span style="font-size: 0.9rem; color: #475569;">Duration: {hours} hrs</span>
             </div>
             """, unsafe_allow_html=True)

    with col2:
        st.subheader("💳 Payment")
        
        if valid_time and amount > 0:
            st.write("Secure Payment Gateway")
            payment_method = st.radio("Select Method", ["UPI", "Credit Card", "Wallet"], horizontal=True)
            
            st.write("")
            if st.button(f"💚 PAY ₹{amount} & BOOK", type="primary", use_container_width=True):
                # Generate Coupon
                coupon = f"CPARK{random.randint(1000, 9999)}"
                
                # Create Booking Record
                booking_record = {
                    "location": loc,
                    "slot_id": slot,
                    "entry_time": str(entry_time),
                    "exit_time": str(exit_time),
                    "duration_hours": hours,
                    "amount": amount,
                    "coupon": coupon,
                    "timestamp": str(datetime.datetime.now()),
                    "status": "confirmed"
                }
                
                # Save
                save_booking(booking_record)
                
                # Success UI
                st.success("✅ Payment Successful!")
                st.balloons()
                
                st.markdown(f"""
                <div style="border: 2px dashed #10b981; padding: 20px; border-radius: 10px; background-color: #ecfdf5; text-align: center;">
                    <h3>🎉 Booking Confirmed!</h3>
                    <p>Your Slot: <b style="font-size: 1.2em;">{slot}</b></p>
                    <p>Time: {entry_time.strftime('%H:%M')} - {exit_time.strftime('%H:%M')}</p>
                    <div style="background-color: white; padding: 10px; font-size: 24px; font-weight: bold; border: 1px solid #ccc; display: inline-block; margin: 10px 0;">
                        {coupon}
                    </div>
                    <p style="margin-top: 10px; font-size: 12px; color: #6b7280;">Show this code at the entry gate.</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.write("")
                if st.button("🏠 Book Another"):
                    st.session_state.booking = {}
                    if "booking_entry" in st.session_state: del st.session_state.booking_entry
                    if "booking_exit" in st.session_state: del st.session_state.booking_exit
                    st.switch_page("pages/1_Home.py")
        else:
            st.warning("Please select valid entry and exit times to proceed.")

if __name__ == "__main__":
    show_confirm()
