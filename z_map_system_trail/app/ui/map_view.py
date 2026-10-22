import math
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsLineItem, QGraphicsSimpleTextItem, QGraphicsItem
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QPen, QBrush, QFont, QPainter

from app.styles import *
from app.models import Spot

class SlotItem(QGraphicsRectItem):
    """Visual representation of a parking slot."""
    def __init__(self, spot: Spot):
        super().__init__(spot.x, spot.y, spot.width, spot.height)
        self.spot = spot
        self.setPen(QPen(QColor(COLOR_BORDER), 1))
        self._update_color()
        
        # Add ID label
        self.label = QGraphicsSimpleTextItem(spot.id, self)
        font = QFont("Segoe UI", 10)
        self.label.setFont(font)
        self.label.setBrush(QBrush(QColor("black"))) # Text color inside slot
        
        # Center the label
        rect = self.rect()
        lb = self.label.boundingRect()
        self.label.setPos(
            rect.x() + (rect.width() - lb.width()) / 2,
            rect.y() + (rect.height() - lb.height()) / 2
        )

    def _update_color(self):
        if self.spot.status == "free":
            c = QColor(COLOR_SLOT_FREE)
        elif self.spot.status == "occupied":
            c = QColor(COLOR_SLOT_OCC)
        else:
            c = QColor(COLOR_SLOT_RESERVED)
        
        self.setBrush(QBrush(c))

    def update_status(self, new_status):
        self.spot.status = new_status
        self._update_color()

class MapView(QGraphicsView):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Setup view implementation
        self.setBackgroundBrush(QBrush(QColor(COLOR_BG_MAIN)))
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw static elements
        self._draw_grid()
        self._draw_lanes()
        
        # Draw slots
        self.slot_items = {}
        for spot in self.model.spots:
            item = SlotItem(spot)
            self.scene.addItem(item)
            self.slot_items[spot.id] = item
            
        # Fit logic can be added later, for now we let it scroll or zoom manually
        # Or simple initial fit:
        # self.fitInView(0, 0, 1920, 1080, Qt.AspectRatioMode.KeepAspectRatio)

    def _draw_grid(self):
        # Draw a subtle grid background like common map UIs
        w, h = 1920, 1080
        step = 40
        pen = QPen(QColor(30, 30, 30), 1)
        
        for x in range(0, w, step):
            self.scene.addLine(x, 0, x, h, pen)
        for y in range(0, h, step):
            self.scene.addLine(0, y, w, y, pen)
            
    def _draw_lanes(self):
        # Draw yellow lane lines
        pen = QPen(QColor("yellow"), 3)
        lane_y = 260
        # Corresponds to: cv2.line(img, (80, lane_y), (W - 80, lane_y), COLOR_LANE, 3)
        self.scene.addLine(80, lane_y, 1920-80, lane_y, pen)
        # Corresponds to: cv2.line(img, (80, lane_y + 200), (W - 80, lane_y + 200), COLOR_LANE, 3)
        self.scene.addLine(80, lane_y + 200, 1920-80, lane_y + 200, pen)

    def refresh_stats(self):
        # If we need to redraw dynamic things
        pass
