"""
Field Observation and Observation Media linking database models.
Distinguishes pilot-verified observations from unverified AI computer-vision detections.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Observation(Base):
    __tablename__ = "observations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id = Column(String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True)
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    source = Column(String(30), nullable=False)  # PILOT, SENSOR, AI
    observation_type = Column(
        String(50), nullable=False
    )  # HUMAN_SIGHTING, HAZARD, STRUCTURAL_DAMAGE, FLOOD_WATER, ACCESS_ROUTE, OBSTACLE
    description = Column(Text, nullable=False)
    
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    verification_status = Column(
        String(30), default="UNVERIFIED_AI", nullable=False
    )  # UNVERIFIED_AI, PILOT_CONFIRMED, OFFICER_VERIFIED
    confidence = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    mission = relationship("Mission", back_populates="observations")
    incident = relationship("Incident", back_populates="observations")
    media_links = relationship("ObservationMedia", back_populates="observation", cascade="all, delete-orphan")


class ObservationMedia(Base):
    __tablename__ = "observation_media"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    observation_id = Column(String(36), ForeignKey("observations.id", ondelete="CASCADE"), nullable=False, index=True)
    media_id = Column(String(36), ForeignKey("media.id", ondelete="CASCADE"), nullable=False, index=True)

    observation = relationship("Observation", back_populates="media_links")
    media = relationship("Media", back_populates="observation_media")
