from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class ParkingSlot(Base):
    __tablename__ = "parking_slots"

    id = Column(String, primary_key=True, index=True) # e.g. "P-A1"
    mall_id = Column(String, index=True)
    slot_label = Column(String) # "A1"
    x = Column(Integer)
    y = Column(Integer)
    is_occupied = Column(Boolean, default=False)
    
    bookings = relationship("Booking", back_populates="slot")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String)
    vehicle_no = Column(String)
    slot_id = Column(String, ForeignKey("parking_slots.id"))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    amount = Column(Float)
    status = Column(String) # "confirmed", "completed", "cancelled"
    qr_code_data = Column(String) # Stores the string for QR generation
    created_at = Column(DateTime, default=datetime.now)

    slot = relationship("ParkingSlot", back_populates="bookings")

class Revenue(Base):
    __tablename__ = "revenue"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.now) # Store just the date usually
    amount = Column(Float)
    mall_id = Column(String)
