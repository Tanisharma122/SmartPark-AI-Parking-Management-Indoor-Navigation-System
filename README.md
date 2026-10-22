# SmartPark: AI Parking Management & Indoor Navigation System

**SmartPark** is an intelligent, end-to-end parking management and indoor navigation platform engineered to streamline parking operations and eliminate driver search time. 

Powered by computer vision and deep learning, the system coordinates distributed edge camera nodes with a central FastAPI backend to deliver real-time slot occupancy monitoring, automated vehicle logging, and seamless wayfinding assistance.

---

## 🌟 Key Capabilities

* **AI Slot Occupancy Detection:** Utilizes lightweight YOLO models across multiple camera zones to detect vehicle presence and track free vs. occupied parking bays in real time.
* **Indoor Wayfinding & Navigation:** Dynamically calculates shortest paths on 2D facility floor maps to guide drivers directly to their designated free space.
* **Contactless Mobile Access:** Motorists simply scan a QR code at the entry gate to open the live interactive navigator on their smartphones without downloading an app.
* **Automatic License Plate Recognition (ANPR):** Integrates YOLO and OCR text recognition to log vehicle entries and exits for automated access control and billing.
* **Live Dashboards:** Features high-visibility LED entrance displays for incoming traffic and comprehensive admin dashboards for facility monitoring.

---

## 📂 Project Architecture

The repository is modularly organized to support end-to-end multi-camera parking operations:

- **`map_Route_Code/` & `map-Rote-Code/`**:
  - `backend/`: Central FastAPI REST API managing slot state, database records, routing, and API key authentication.
  - `camera_node/`: Edge camera stream processors (`camera1`, `camera2`) running YOLO detection and sending slot status payloads.
  - `dashboard/`: Streamlit LED entrance display (`dashboard.py`) and turn-by-turn mobile wayfinder (`navigator.py`).
  - `start_secure_tunnel.py` & `generate_qr_code.py`: Tunneling and QR code generation for mobile access at the entrance.
- **`licence_detection/`**: Automated License Plate Recognition (ANPR) pipeline utilizing YOLOv8 and EasyOCR.
- **`advance_booking/`**: Advance reservation module with location distance calculations and booking management.
- **`z_map_system_trail/`**: Desktop UI application built with PyQt6 for real-time map rendering and visual monitoring.
- **`yolo11-parkinglot-main/`**: Parking bay ROI delineation and slot counting modules.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- PyTorch & Ultralytics
- OpenCV, FastAPI, Uvicorn, Streamlit

### 2. Installation
```bash
pip install -r map_Route_Code/requirements.txt
```

### 3. Running the System
1. **Start Backend Service:**
   ```bash
   cd map_Route_Code/backend
   uvicorn app:app --reload
   ```
2. **Launch Edge Cameras:**
   ```bash
   python map_Route_Code/camera_node/camera1/main.py
   python map_Route_Code/camera_node/camera2/main.py
   ```
3. **Launch Dashboards:**
   ```bash
   streamlit run map_Route_Code/dashboard/dashboard.py --server.port 8501
   streamlit run map_Route_Code/dashboard/navigator.py --server.port 8502
   ```

---

## 🔑 Security
Device nodes and dashboard consumers interact via API key authorization (`X-API-KEY` header). See `map_Route_Code/README.md` for credential configurations.
