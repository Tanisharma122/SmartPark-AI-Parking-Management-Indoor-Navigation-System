# 🚗 Smart Parking Management System

This professional parking solution uses AI-powered camera nodes to detect free spaces and a centralized backend to coordinate LED dashboards and user navigation.

---

## 📂 Project Structure

- **`/backend`**: The core API (FastAPI) that manages the database, security keys, and navigation logic.
- **`/camera_node`**:
    - `camera1`: Primary entrance camera (detects P1, P2, P3).
    - `camera2`: Secondary camera (detects P17, P28, etc.).
- **`/dashboard`**:
    - `dashboard.py`: Interactive LED Screen for use at the entrance.
    - `navigator.py`: Premium User Wayfinder with maps and driving directions.
- **`test_api.py`**: Utility script to check if your Security Key is active.

---

## 🚀 Execution Guide

Follow these steps in order to start the system:

### 1. Start the Backend (Must be first)
Open a terminal and run:
```powershell
cd backend
uvicorn app:app --reload
```
*The API will be live at: http://127.0.0.1:8000*

### 2. Start Camera Nodes
Open two separate terminals and run:
```powershell
# Camera 1
cd camera_node/camera1
python main.py

# Camera 2
cd camera_node/camera2
python main.py
```

### 3. Open the Dashboards
Open two more terminals and run:
```powershell
# LED Entrance Screen
cd dashboard
streamlit run dashboard.py --server.port 8501

# User Wayfinder (Navigator)
cd dashboard
streamlit run navigator.py --server.port 8502
```

---

## 🔑 Security & APIs

Your system is protected via an **X-API-KEY** header. Use the following credentials:

- **API Key**: `sp_live_3fa85f64a12b9d9a8e5f3c2b1a0d4e6f`
- **Header Name**: `X-API-KEY`

### 🛠️ Method 1: Automatic Test Script
You can verify the system and API Key instantly by running:
```powershell
python test_api.py
```
*This will check both the Dashboard and Navigation data connectivity.*

### 🌐 Method 2: Browser Testing (Swagger UI)
Visit the interactive documentation link in Google Chrome:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

**Steps to see results:**
1. Click the green **Authorize** button (top right).
2. Paste `sp_live_3fa85f64a12b9d9a8e5f3c2b1a0d4e6f` into the Value field.
3. Click **Authorize** -> **Close**.
4. Scroll to **Dashboard** -> **GET `/active-free-slots`**.
5. Click **Try it out** -> **Execute**.

### 🔗 Magic Links (Works Directly in Browser)
Click these links to see the live results without any setup:
- **Live Slots**: [http://127.0.0.1:8000/active-free-slots?api_key=sp_live_3fa85f64a12b9d9a8e5f3c2b1a0d4e6f](http://127.0.0.1:8000/active-free-slots?api_key=sp_live_3fa85f64a12b9d9a8e5f3c2b1a0d4e6f)
- **Nav Graph**: [http://127.0.0.1:8000/navigation-data?api_key=sp_live_3fa85f64a12b9d9a8e5f3c2b1a0d4e6f](http://127.0.0.1:8000/navigation-data?api_key=sp_live_3fa85f64a12b9d9a8e5f3c2b1a0d4e6f)

---

## 🔳 QR Code & Mobile Access

Drivers can scan a QR code at the gate to open the **Smart Wayfinder** on their phones. To ensure a professional experience without "Not Secure" warnings, follow these steps:

### 1. Create a Secure Tunnel (HTTPS)
Open a new terminal and run:
```powershell
ssh -R 80:localhost:8502 nokey@localhost.run
```
*Wait for the terminal to show a link like `https://...lhr.life`. **Copy this link.***

### 2. Generate the QR Code
Run the generator script:
```powershell
python generate_qr_code.py
```
When prompted, **paste the HTTPS link** you copied in Step 1.

### 3. Display at Gate
A file named `parking_gate_qr.png` will be created. You can print this or display it at the entrance. When drivers scan it, the navigator will open securely with **no browser warnings**.

---

## 💡 System Logic

1. **Priority Rule**: The system always prioritizes **CAM_1**. If even one spot (like P2) is free in CAM_1, the dashboard will hide CAM_2 slots to keep the entrance efficient.
2. **Multi-Camera Navigation**: The "Smart Wayfinder" now supports both cameras. When Primary is full, the map automatically switches to the **Secondary Layout (vid4)**.
3. **Safe Navigation (CAM_1)**: For the primary entrance, the system forces a Right Turn to avoid the subterranean exit lane.
4. **Automatic Map Sync**: The system uses real-time reference frames (`arial2.jpg` for CAM_1, `vid4.jpg` for CAM_2) to ensure the path is always drawn on the correct visual layout.
5. **Ghost Prevention**: When a camera restarts, it automatically clears its old database records to ensure you never see "ghost" slots.
6. **Real-time Refresh**: Dashboards update every **0.5 seconds** automatically.
