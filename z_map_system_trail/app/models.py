from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Spot:
    id: str
    x: float
    y: float
    width: float
    height: float
    status: str = "free" # free, occupied, unknown
    angle: float = 0.0

@dataclass
class Zone:
    id: str
    coords: List[Tuple[float, float]]
    type: str # lane, no_parking, walkway

class ParkingLotModel:
    def __init__(self):
        self.spots: List[Spot] = []
        self.zones: List[Zone] = []
        self.width = 1920
        self.height = 1080
        
        # Load initial mock data based on map1.py logic
        self._init_demo_data()
        
    def _init_demo_data(self):
        # Replicating map1.py structure
        
        # Top Row
        slot_w, slot_h, gap = 60, 100, 12
        start_x_top, start_y_top = 280, 120
        statuses_top = ["free", "occupied", "occupied", "free", "free", "occupied", "free", "occupied", "free", "occupied"]
        
        for i, status in enumerate(statuses_top):
            s = Spot(
                id=f"S{i+1}",
                x=start_x_top + i * (slot_w + gap),
                y=start_y_top,
                width=slot_w,
                height=slot_h,
                status=status
            )
            self.spots.append(s)

        # Lane Y reference from map1.py is 260
        lane_y = 260
        
        # Middle Row
        start_x_mid = 280
        start_y_mid = lane_y + 20
        # "occ" if i % 2 else "free"
        for i in range(10):
            status = "occupied" if i % 2 else "free"
            s = Spot(
                id=f"S{11+i}",
                x=start_x_mid + i * (slot_w + gap),
                y=start_y_mid,
                width=slot_w,
                height=slot_h,
                status=status
            )
            self.spots.append(s)
            
        # Bottom Row
        start_x_bot = 280
        start_y_bot = lane_y + 220
        for i in range(10):
            s = Spot(
                id=f"S{21+i}",
                x=start_x_bot + i * (slot_w + gap),
                y=start_y_bot,
                width=slot_w,
                height=slot_h,
                status="free"
            )
            self.spots.append(s)
            
    def get_stats(self):
        total = len(self.spots)
        free = sum(1 for s in self.spots if s.status == "free")
        occupied = sum(1 for s in self.spots if s.status == "occupied")
        return {"total": total, "free": free, "occupied": occupied}
