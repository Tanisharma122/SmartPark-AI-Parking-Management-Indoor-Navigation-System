from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QProgressBar, QFrame, QPushButton
from PyQt6.QtCore import Qt
from app.styles import *

class SidePanel(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setObjectName("SidePanel")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        
        # Header
        self.header = QLabel(title)
        self.header.setObjectName("PanelHeader")
        self.layout.addWidget(self.header)
        
        # Content Container
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.layout.addWidget(self.content)
        self.layout.addStretch()

class StatsPanel(SidePanel):
    def __init__(self):
        super().__init__("Occupancy")
        
        self.total_lbl = QLabel("Total: 0")
        self.free_lbl = QLabel("Vacant: 0")
        self.occ_lbl = QLabel("Occupied: 0")
        
        # Style these big
        font = self.total_lbl.font()
        font.setPointSize(12)
        self.total_lbl.setFont(font)
        
        self.content_layout.addWidget(self.total_lbl)
        self.content_layout.addWidget(self.free_lbl)
        self.content_layout.addWidget(self.occ_lbl)
        
        # Progress Bar
        self.pbar = QProgressBar()
        self.pbar.setRange(0, 100)
        self.pbar.setValue(0)
        self.pbar.setFormat("%p% Full")
        self.content_layout.addWidget(self.pbar)
        
    def update_stats(self, stats):
        total = stats['total']
        free = stats['free']
        occ = stats['occupied']
        
        self.total_lbl.setText(f"Total: {total}")
        self.free_lbl.setText(f"<font color='{COLOR_SLOT_FREE}'>Vacant: {free}</font>")
        self.occ_lbl.setText(f"<font color='{COLOR_SLOT_OCC}'>Occupied: {occ}</font>")
        
        if total > 0:
            perc = int((occ / total) * 100)
            self.pbar.setValue(perc)

class FloorPanel(SidePanel):
    def __init__(self):
        super().__init__("Parking Floors")
        
        floors = ["Floor B1", "Floor B2", "Floor B3"]
        self.list = QListWidget()
        for f in floors:
            self.list.addItem(f)
        self.list.setCurrentRow(0)
        
        self.content_layout.addWidget(self.list)
