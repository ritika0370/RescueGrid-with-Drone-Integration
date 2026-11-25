"""
Drone Station and Drone Registry database models.
Tracks physical/simulated drone telemetry, operational statuses, and battery health.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base


class DroneStation(Base):
    __tablename__ = "drone_stations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(120), nullable=False, unique=True)
    department_id = Column(String(36), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String(30), default="OPERATIONAL")  # OPERATIONAL, LIMITED, OFFLINE
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    department = relationship("Department", back_populates="drone_stations")
    drones = relationship("Drone", back_populates="station", cascade="all, delete-orphan")
    missions = relationship("Mission", back_populates="station")


class Drone(Base):
    __tablename__ = "drones"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model = Column(String(100), nullable=False)
    station_id = Column(String(36), ForeignKey("drone_stations.id", ondelete="SET NULL"), nullable=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    battery_percentage = Column(Float, default=100.0, nullable=False)
    availability_status = Column(
        String(30), default="AVAILABLE", index=True
    )  # AVAILABLE, ASSIGNED, PREPARING, IN_FLIGHT, RETURNING, CHARGING, OFFLINE, MAINTENANCE
    max_range_km = Column(Float, default=15.0)
    max_flight_time_min = Column(Integer, default=35)
    last_telemetry_at = Column(DateTime, nullable=True)
    is_simulated = Column(Boolean, default=True, nullable=False)  # Explicitly label simulated telemetry
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    station = relationship("DroneStation", back_populates="drones")
    missions = relationship("Mission", back_populates="drone")
