import sqlite3
import os

db_path = "backend/parking.db"
if os.path.exists(db_path):
    try:
        os.remove(db_path)
        print(f"Deleted existing {db_path}")
    except PermissionError:
        print(f"Warning: Could not delete {db_path} (in use). Attempting to re-initialize tables.")

# Import and run init from database.py
import sys
sys.path.append('backend')
from database import init

init()
print("Database re-initialized with VIDEO-CENTRIC schema.")

# Populate with initial data
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 1. Organization
cur.execute("INSERT INTO organizations (org_id, name) VALUES (?, ?)", ("ORG_001", "Main Organization"))

# 2. Basement
cur.execute("""
    INSERT INTO basements (basement_id, org_id, name, latitude, longitude) 
    VALUES (?, ?, ?, ?, ?)
""", ("BASE_001", "ORG_001", "Ground Floor Parking", 19.0760, 72.8777))


# 3. Videos (was Cameras)
cur.execute("""
    INSERT INTO videos (video_id, basement_id, type, source, latitude, longitude, lanes_file, slots_file, image_file) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    "VID_1", "BASE_001", "video", "camera1/arial11.mp4", 19.0761, 72.8778,
    r"c:\Users\JIYA SONI\Desktop\detector1\map Rote Code\camera_node\camera1\lanes.json",
    r"c:\Users\JIYA SONI\Desktop\detector1\map Rote Code\camera_node\camera1\arial11.json",
    "arial2.jpg"
))

cur.execute("""
    INSERT INTO videos (video_id, basement_id, type, source, latitude, longitude, lanes_file, slots_file, image_file) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    "VID_2", "BASE_001", "video", "camera2/vid4.mp4", 19.0762, 72.8779,
    r"c:\Users\JIYA SONI\Desktop\detector1\map Rote Code\camera_node\camera2\vid4_lanes.json",
    r"c:\Users\JIYA SONI\Desktop\detector1\map Rote Code\camera_node\camera2\vid4.json",
    "vid4.jpg"
))

# 4. API Keys
# ORG API KEY
cur.execute("""
    INSERT INTO api_keys (key, key_type, target_id, owner, is_active) 
    VALUES (?, ?, ?, ?, ?)
""", ("sk_org_dashboard_123", "org", "ORG_001", "Admin Dashboard", 1))

# DEVICE API KEY for VID_1
cur.execute("""
    INSERT INTO api_keys (key, key_type, target_id, owner, is_active) 
    VALUES (?, ?, ?, ?, ?)
""", ("sk_dev_vid1_456", "device", "VID_1", "Video 1 Feed", 1))

# DEVICE API KEY for VID_2
cur.execute("""
    INSERT INTO api_keys (key, key_type, target_id, owner, is_active) 
    VALUES (?, ?, ?, ?, ?)
""", ("sk_dev_vid2_789", "device", "VID_2", "Video 2 Feed", 1))

conn.commit()
conn.close()
print("Initial video-centric data populated.")
