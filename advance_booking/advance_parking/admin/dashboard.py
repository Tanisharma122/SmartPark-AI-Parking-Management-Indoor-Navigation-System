import streamlit as st
import json
import pandas as pd
import plotly.express as px

def load_data():
    try:
        with open("data/bookings.json", 'r') as f:
            return pd.DataFrame(json.load(f))
    except:
        return pd.DataFrame()

def show_admin():
    st.set_page_config(page_title="Admin Dashboard", layout="wide")
    st.title("🛡️ Admin Dashboard")
    
    st.markdown("### 📊 Live Statistics")
    
    df = load_data()
    
    col1, col2, col3 = st.columns(3)
    
    if not df.empty:
        total_bookings = len(df)
        total_revenue = df['amount'].sum()
        active_now = len(df) # Logic could be improved based on timestamps
        
        col1.metric("Total Bookings", total_bookings)
        col2.metric("Total Revenue", f"₹{total_revenue}")
        col3.metric("Live Active", active_now) # Placeholder logic
        
        st.write("---")
        st.subheader("Recent Bookings")
        st.dataframe(df.sort_values(by="timestamp", ascending=False), use_container_width=True)
        
        # Charts
        st.write("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Revenue by Location")
            if 'location' in df.columns:
                fig = px.pie(df, names='location', values='amount')
                st.plotly_chart(fig, use_container_width=True)
                
    else:
        st.info("No bookings data available yet.")
        
    if st.button("🔄 Refresh Data"):
        st.rerun()

if __name__ == "__main__":
    show_admin()
