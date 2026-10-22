from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QMainWindow
from app.ui.map_view import MapView
from app.ui.panels import StatsPanel, FloorPanel
from app.models import ParkingLotModel
from app.styles import *

class Dashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HikCentral Professional Web Client - Parking Lot 1")
        self.resize(1600, 900)
        
        # Central Widget & Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Data Model
        self.model = ParkingLotModel()
        
        # 1. Left Panel (Floors)
        self.left_panel = FloorPanel()
        self.left_panel.setFixedWidth(250)
        main_layout.addWidget(self.left_panel)
        
        # 2. Center (Map)
        self.map_view = MapView(self.model)
        main_layout.addWidget(self.map_view, stretch=1)
        
        # 3. Right Panel (Stats)
        self.right_panel = StatsPanel()
        self.right_panel.setFixedWidth(300)
        main_layout.addWidget(self.right_panel)
        
        # Initial stats update
        self.right_panel.update_stats(self.model.get_stats())
