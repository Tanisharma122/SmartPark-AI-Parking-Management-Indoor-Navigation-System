# config.py

# Camera identity
CAMERA_ID = "cam1"

# Paths
VIDEO_PATH = "arial2.mp4"       # in same folder
MODEL_PATH = "best.pt"         # your trained model
SLOTS_JSON = "arial2.json"      # slot polygons with slot_id + points

# Frame size (match your training / JSON)
FRAME_WIDTH = 1080
FRAME_HEIGHT = 600

# YOLO/parking manager thresholds
CONF_THRES = 0.25
IOU_THRES = 0.6

# How often to send data to backend (seconds)
SEND_INTERVAL = 2.0
