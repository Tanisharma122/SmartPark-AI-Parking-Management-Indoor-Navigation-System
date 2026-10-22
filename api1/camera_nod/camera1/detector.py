# detector.py
from ultralytics import solutions

def load_manager(model_path, slots_json, conf_thres, iou_thres):
    """
    Wrap Ultralytics ParkingManagement for your camera.
    """
    pm = solutions.ParkingManagement(
        model=model_path,
        json_file=slots_json,
        conf=conf_thres,
        iou=iou_thres,
        show=False,
    )
    return pm
