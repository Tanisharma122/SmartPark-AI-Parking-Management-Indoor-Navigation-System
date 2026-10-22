# 🚗 Smart Parking Management System (Video-Centric)

This professional parking solution uses AI-powered video stream processing to detect free spaces across multiple zones (VID_1, VID_2) and coordinates data through a centralized backend for LED dashboards and real-time user navigation.

---

## 📂 Project Structure

- **`/backend`**: The core API (FastAPI) managing the video database, security keys, and pathfinding logic.
- **`/camera_node`**:
    - `camera1`: Video processor for **VID_1** (Entrance Zone).
    - `camera2`: Video processor for **VID_2** (Extended Zone).
- **`/dashboard`**:
    - `dashboard.py`: LED Status Display (Shows available spots from all videos).
    - `navigator.py`: Premium User Wayfinder with dynamic maps and driving directions.
- **`test_api.py`**: Utility script to verify Video/Org API permissions.

---

## 🚀 Execution Guide

### 1. Start the Backend
```powershell
uvicorn backend.app:app --reload
```

### 2. Start Video Nodes (Simulated or Live)
```powershell
python camera_node/camera1/main.py
python camera_node/camera2/main.py
```

### 3. Open the Dashboards
```powershell
# LED Availability View
streamlit run dashboard/dashboard.py --server.port 8501

# Driver Navigator
streamlit run dashboard/navigator.py --server.port 8502
```
---

## 🔑 Security & API Directory

The system uses a two-tier **x-api-key** structure.

### 🏢 Organization Master View (Org Key: `sk_org_dashboard_123`)
*   **Combined Free Slots:** [http://localhost:8000/active-free-slots?api_key=sk_org_dashboard_123](http://localhost:8000/active-free-slots?api_key=sk_org_dashboard_123)
*   **Video Feed Directory:** [http://localhost:8000/videos-list?api_key=sk_org_dashboard_123](http://localhost:8000/videos-list?api_key=sk_org_dashboard_123)

### 🎥 Video Specific Status (Device Keys)
*   **VID_1 Status (Key: `sk_dev_vid1_456`):** [http://localhost:8000/video-free-slots/VID_1?api_key=sk_dev_vid1_456](http://localhost:8000/video-free-slots/VID_1?api_key=sk_dev_vid1_456)
*   **VID_2 Status (Key: `sk_dev_vid2_789`):** [http://localhost:8000/video-free-slots/VID_2?api_key=sk_dev_vid2_789](http://localhost:8000/video-free-slots/VID_2?api_key=sk_dev_vid2_789)

**Sample Response:**
```json
{
    "video_id": "VID_1",
    "status": "Online",
    "free_slots": ["P2", "P5"],
    "reserved_slots": ["P1"]
}
```

---

## 🔳 Mobile Access & Remote Setup

To give drivers access outside your local network:

1.  **Start the Secure Tunnel:**
    ```powershell
    python start_secure_tunnel.py
    ```
    *This will create an HTTPS link and update `parking_gate_qr.png` automatically.*

2.  **Display the QR Code:**
    Drivers scan the QR to open the **Navigator** on their mobile devices without security warnings.

---

## 💡 System Logic (Video-Centric)

1.  **Unified Dashboard**: The LED dashboard now combines free spots from **all** active video feeds (multi-view) instead of switching between them.
2.  **Granular Security**: Device keys can only see their own assigned video data. Org keys have master visibility.
3.  **Real-time Expiry**: Slots are considered "Live" only if updated in the last **30 seconds**.
4.  **Pretty JSON**: All API responses are automatically formatted (indented) for easier debugging and integration.
5.  **Dynamic Map Switching**: The Navigator automatically loads the correct background (`arial2.jpg` or `vid4.jpg`) based on the target slot's video source.
