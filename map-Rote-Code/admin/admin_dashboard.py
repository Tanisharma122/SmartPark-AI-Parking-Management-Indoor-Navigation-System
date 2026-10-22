import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

# ---------- CONFIG ----------
BACKEND_URL = "http://127.0.0.1:8000/admin"

st.set_page_config(page_title="SaaS Super Admin", layout="wide")

# ---------- STYLING ----------
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        padding: 40px;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #f3f4f6;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- STATE MGMT ----------
if "view_detail" not in st.session_state:
    st.session_state.view_detail = None

# ---------- TABS ----------
tab_overview, tab_manage, tab_add, tab_logs = st.tabs(["🌎 Global Overview", "🏢 Manage Clients", "➕ Rapid Setup", "📜 System Logs"])

with tab_overview:
    st.markdown('<div class="main-header"><h1>Admin Dashboard</h1></div>', unsafe_allow_html=True)
    
    try:
        stats = requests.get(f"{BACKEND_URL}/stats").json()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button(f"🏢 Clients: {stats['total_organizations']}", use_container_width=True):
                st.session_state.view_detail = "orgs"
        with col2:
            if st.button(f"🏗️ Basements: {stats['total_basements']}", use_container_width=True):
                st.session_state.view_detail = "basements"
        with col3:
            if st.button(f"🎥 Total Cameras: {stats['total_cameras']}", use_container_width=True):
                st.session_state.view_detail = "cameras"
        with col4:
            if st.button(f"🟢 Live Now: {stats['cameras_active_last_min']}", use_container_width=True):
                st.session_state.view_detail = "live"
            
        st.markdown("---")

        # Dynamic Results Section
        if st.session_state.view_detail == "orgs":
            st.write("### 🏢 Registered Organizations")
            data = requests.get(f"{BACKEND_URL}/organizations").json()
            st.table(pd.DataFrame(data))

        elif st.session_state.view_detail == "basements":
            st.write("### 🏗️ All Registered Basements/Zones")
            data = requests.get(f"{BACKEND_URL}/all-basements").json()
            st.table(pd.DataFrame(data))
        
        elif st.session_state.view_detail == "cameras" or st.session_state.view_detail == "live":
            st.write(f"### 🎥 System-wide Camera Registry ({st.session_state.view_detail})")
            data = requests.get(f"{BACKEND_URL}/all-cameras").json()
            df = pd.DataFrame(data)
            if st.session_state.view_detail == "live":
                df = df[df["status"] == "Online"]
            st.dataframe(df, use_container_width=True)

            with st.expander("🗑️ Clean Registry (Delete Camera)"):
                kill_id = st.text_input("Enter Camera ID to permanently delete", placeholder="e.g. cam1")
                if st.button("Delete Camera Now", type="secondary"):
                    if kill_id:
                        res = requests.delete(f"{BACKEND_URL}/delete-video/{kill_id}").json()
                        st.success(res["message"])
                        time.sleep(1)
                        st.rerun()

    except Exception as e:
        st.error(f"Sync error: {e}")

with tab_manage:
    st.subheader("Client Hierarchy & Provisioning")
    base_api_url = "http://127.0.0.1:8000" # Update this when deploying
    try:
        orgs = requests.get(f"{BACKEND_URL}/organizations").json()
        if orgs:
            for org in orgs:
                org_name = org["name"]
                org_id = org["org_id"]
                
                with st.expander(f"🏢 {org_name} (ID: {org_id})", expanded=False):
                    details = requests.get(f"{BACKEND_URL}/organization-details/{org_id}").json()
                    
                    col_info, col_keys = st.columns([1, 1])
                    
                    with col_info:
                        st.markdown("#### 📍 Infrastructure")
                        for b in details["basements"]:
                            b_id = b['basement_id']
                            st.markdown(f"**🏗️ {b['name']}** (`{b_id}`)")
                            
                            # Interactive "Add Camera" for THIS basement
                            new_cam = st.text_input("New Camera ID", key=f"input_{b_id}", placeholder="e.g. VID_5")
                            if st.button("➕ Register Camera here", key=f"btn_{b_id}"):
                                if new_cam:
                                    res = requests.post(f"{BACKEND_URL}/add-video?basement_id={b_id}&video_id={new_cam}").json()
                                    st.success(f"Registered! Key: {res['device_api_key']}")
                                    time.sleep(1)
                                    st.rerun()

                            if b["videos"]:
                                for v in b["videos"]:
                                    v_id = v['video_id']
                                    is_active = v.get("is_active", 0)
                                    status_icon = "🟢" if is_active else "🔴"
                                    
                                    # Create a layout with Name & Toggle
                                    col_cam, col_switch = st.columns([3, 1])
                                    with col_cam:
                                        # Locate the device key for this specific video (using target_id)
                                        d_key = next((k["key"] for k in details["api_keys"] if k["target_id"] == v_id), "NO_KEY")
                                        if d_key != "NO_KEY":
                                            slot_url = f"{base_api_url}/video-free-slots/{v_id}?api_key={d_key}"
                                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{status_icon} `{v_id}` — [Free Slot API]({slot_url})")
                                        else:
                                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{status_icon} `{v_id}` — ⚠️ **No API Key**")
                                    
                                    with col_switch:
                                        btn_label = "🔴 Stop" if is_active else "🟢 Start"
                                        if st.button(btn_label, key=f"tog_{v_id}", use_container_width=True):
                                            new_state = 0 if is_active else 1
                                            requests.post(f"{BACKEND_URL}/toggle-video/{v_id}?active={new_state}")
                                            st.rerun()
                                            
                                    if d_key == "NO_KEY":
                                        if st.button(f"🔑 Fix/Regenerate Key for {v_id}", key=f"fix_{v_id}"):
                                            res = requests.post(f"{BACKEND_URL}/add-video?basement_id={b_id}&video_id={v_id}").json()
                                            st.success("New Key Generated!")
                                            time.sleep(1)
                                            st.rerun()
                            else:
                                st.caption("&nbsp;&nbsp;&nbsp;&nbsp;No cameras assigned yet.")
                    
                    with col_keys:
                        st.markdown("#### 🔑 Sharing & API Portal")
                        org_keys = [k for k in details["api_keys"] if k["key_type"] == "org"]
                        dev_keys = [k for k in details["api_keys"] if k["key_type"] == "device"]

                        if org_keys:
                            o_key = org_keys[0]["key"]
                            st.write("**Master Key (For LED/Apps):**")
                            st.code(o_key)
                            master_url = f"{base_api_url}/active-free-slots?api_key={o_key}"
                            st.markdown(f"🔗 [Open Master Live Feed]({master_url})")
                        
                        if dev_keys:
                            st.write("**Specific Device Keys (Copy-Paste):**")
                            for k in dev_keys:
                                v_id = k["target_id"]
                                d_key = k["key"]
                                st.code(f"# {v_id} Config\nDEVICE_API_KEY = \"{d_key}\"")

            st.markdown("---")
            st.subheader("🗑️ Danger Zone")
            del_id = st.text_input("Confirm Organization ID to wipe data", key="del_org_id").strip().upper()
            if st.button("Permanently Delete Client", type="secondary", help="Warning: Cascaded deletion!"):
                if del_id:
                    res = requests.delete(f"{BACKEND_URL}/delete-organization/{del_id}").json()
                    if res.get("status") == "success":
                        st.success(res["message"])
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(res.get("detail", "Error deleting."))
                else:
                    st.warning("Enter ID first.")
        else:
            st.info("No organizations registered yet.")
    except Exception as e:
        st.error(f"Error loading client data: {e}")

with tab_add:
    st.subheader("Onboard New Client")
    with st.expander("Step 1: Create Organization", expanded=True):
        org_name = st.text_input("Organization Name", placeholder="e.g. Phoenix Mall")
        if st.button("Generate Organization"):
            if org_name:
                resp = requests.post(f"{BACKEND_URL}/create-organization?name={org_name}")
                res = resp.json()
                if resp.status_code == 200:
                    st.success(f"Organization Created! ID: {res['org_id']}")
                    st.code(f"Dashboard API Key: {res['api_key']}", language="text")
                else:
                    st.error(f"Failed to create organization: {res.get('detail', 'Unknown error')}")
            else:
                st.warning("Please enter a name.")

    with st.expander("Step 2: Add Basement / Zone"):
        target_org = st.text_input("Paste Organization ID")
        b_name = st.text_input("Basement Name", placeholder="e.g. Lower Ground B2")
        if st.button("Add Basement"):
            if target_org and b_name:
                resp = requests.post(f"{BACKEND_URL}/add-basement?org_id={target_org}&name={b_name}")
                res = resp.json()
                if resp.status_code == 200:
                    st.success(f"Basement Added! ID: {res['basement_id']}")
                else:
                    st.error(f"Failed to add basement: {res.get('detail', 'Unknown error')}")
            else:
                st.warning("All fields required.")

    with st.expander("Step 3: Register Camera Node"):
        target_base = st.text_input("Paste Basement ID")
        cam_id = st.text_input("Camera ID (Unique name)", placeholder="e.g. CAM_ENT_01")
        if st.button("Provision Camera"):
            if target_base and cam_id:
                resp = requests.post(f"{BACKEND_URL}/add-video?basement_id={target_base}&video_id={cam_id}")
                res = resp.json()
                if resp.status_code == 200:
                    st.success("Camera Provisioned Successfully!")
                    st.write("### 🔑 Copy this to camera config.py")
                    st.code(f"""
# Camera Configuration
VIDEO_ID = "{res['video_id']}"
DEVICE_API_KEY = "{res['device_api_key']}"
BACKEND_URL = "http://YOUR_SERVER_IP:8000"
                    """, language="python")
                else:
                    st.error(f"Failed to provision camera: {res.get('detail', 'Unknown error')}")
            else:
                st.warning("All fields required.")

with tab_logs:
    st.subheader("📜 Global System Activity")
    st.write("Real-time monitoring of errors and system events.")
    
    try:
        resp = requests.get(f"{BACKEND_URL}/logs")
        if resp.status_code == 200:
            logs_data = resp.json()
            if logs_data:
                df_logs = pd.DataFrame(logs_data)
                # Ensure all columns exist to prevent KeyError
                target_cols = ['org_name', 'timestamp', 'level', 'source', 'message']
                existing_cols = [c for c in target_cols if c in df_logs.columns]
                df_logs = df_logs[existing_cols]
                
                # Format timestamp
                if 'timestamp' in df_logs.columns:
                    df_logs['timestamp'] = df_logs['timestamp'].apply(lambda x: datetime.fromtimestamp(x).strftime('%H:%M:%S'))
                
                st.dataframe(df_logs, use_container_width=True)
            else:
                st.info("Log registry is currently empty.")
        else:
            st.error(f"Backend Error ({resp.status_code}): {resp.text}")
            
        # Manually Add Log (Developer Tool)
        with st.expander("🛠️ Developer Tool: Publish Test Log"):
            col_l, col_s, col_o = st.columns(3)
            lvl = col_l.selectbox("Severity", ["INFO", "WARNING", "ERROR", "CRITICAL"])
            src = col_s.text_input("Source Component", value="Admin_UI")
            o_id = col_o.text_input("Simulate Org ID", value="ORG_001")
            msg = st.text_input("Log Message", placeholder="Everything is looking good...")
            if st.button("Send to Log Registry"):
                requests.post(f"{BACKEND_URL}/add-log?level={lvl}&source={src}&message={msg}&org_id={o_id}")
                st.success("Event Recorded")
                time.sleep(1)
                st.rerun()
    except Exception as e:
        st.error(f"Integrity Error: {e}")

st.sidebar.markdown("---")
st.sidebar.info("Logged in as: Super Admin")
if st.sidebar.button("Refresh Monitor"):
    st.rerun()

time.sleep(10)
st.rerun()
