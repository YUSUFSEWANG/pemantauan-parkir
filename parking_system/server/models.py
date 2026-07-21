"""
Model data untuk lahan parkir kampus dan riwayat okupansinya.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class ParkingLot(Base):
    """Representasi satu lahan/gedung parkir kampus (satu titik/node distribusi)."""
    __tablename__ = "parking_lots"

    id = Column(String, primary_key=True)          # contoh: "GKU", "FT-A", "REKTORAT"
    name = Column(String, nullable=False)
    location = Column(String, nullable=True)
    total_slots = Column(Integer, nullable=False, default=0)
    occupied_slots = Column(Integer, nullable=False, default=0)
    node_id = Column(String, nullable=True)          # id agent/node yang melapor
    last_update = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="unknown")        # online / offline

    history = relationship("ParkingHistory", back_populates="lot", cascade="all, delete-orphan")

    @property
    def available_slots(self):
        return max(self.total_slots - self.occupied_slots, 0)

    @property
    def occupancy_rate(self):
        if self.total_slots == 0:
            return 0.0
        return round((self.occupied_slots / self.total_slots) * 100, 1)


class ParkingHistory(Base):
    """Log riwayat perubahan okupansi tiap lahan parkir (time-series)."""
    __tablename__ = "parking_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lot_id = Column(String, ForeignKey("parking_lots.id"), nullable=False)
    occupied_slots = Column(Integer, nullable=False)
    total_slots = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    node_id = Column(String, nullable=True)

    lot = relationship("ParkingLot", back_populates="history")
