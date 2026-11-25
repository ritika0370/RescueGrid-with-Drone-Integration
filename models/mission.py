"""
Drone Mission and Job Card database model.
Supports the manual pilot survey workflow from job card creation through completion.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Mission(Base):
    __tablename__ = "missions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    drone_id = Column(String(36), ForeignKey("drones.id", ondelete="SET NULL"), nullable=True, index=True)
    station_id = Column(String(36), ForeignKey("drone_stations.id", ondelete="SET NULL"), nullable=True)
    pilot_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Structured Job Card payload
    job_card_json = Column(JSON, nullable=False)
    mission_mode = Column(String(30), default="MANUAL_SURVEY", nullable=False)
    
    # State Machine
    status = Column(
        String(30), default="CREATED", index=True
    )  # CREATED, ASSIGNED, ACCEPTED, REJECTED, PREPARING, IN_FLIGHT, PAUSED, COMPLETED, CANCELLED
    rejection_reason = Column(Text, nullable=True)
    pilot_notes = Column(Text, nullable=True)
    scanned_boundary_geojson = Column(JSON, nullable=True)
    
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    incident = relationship("Incident", back_populates="missions")
    drone = relationship("Drone", back_populates="missions")
    station = relationship("DroneStation", back_populates="missions")
    pilot = relationship("User", back_populates="assigned_missions", foreign_keys=[pilot_id])
    observations = relationship("Observation", back_populates="mission", cascade="all, delete-orphan")
    media_items = relationship("Media", back_populates="mission")
    ai_analyses = relationship("AIAnalysis", back_populates="mission")
