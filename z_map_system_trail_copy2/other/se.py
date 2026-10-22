from ultralytics import solutions

# This opens a Tkinter GUI:
# 1) It will ask you to choose an IMAGE (your parking frame)
# 2) Left-click to add polygon points for each slot
# 3) Press "n" or GUI button to start a new slot
# 4) Press "s" or click "save" to export JSON (e.g., img0.json)
solutions.ParkingPtsSelection()
