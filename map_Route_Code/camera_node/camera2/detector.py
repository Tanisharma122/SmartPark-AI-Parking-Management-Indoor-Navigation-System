from ultralytics import solutions

def load_manager(model, json_file, conf, iou):
    return solutions.ParkingManagement(
        model=model,
        json_file=json_file,
        conf=conf,
        iou=iou,
        show=False
    )
