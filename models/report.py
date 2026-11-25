"""
Citizen Emergency SOS Report model.
Preserves independent records, original GPS coordinates, descriptions, and media.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reporter_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    reporter_phone = Column(String(30), nullable=True)
    reporter_name = Column(String(100), nullable=True)
    emergency_category = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False)
    
    # Precise Location Information
    latitude = Column(Float, nullable=True, index=True)
    longitude = Column(Float, nullable=True, index=True)
    location_accuracy = Column(Float, nullable=True)
    manually_entered_location = Column(String(255), nullable=True)
    address_or_landmark = Column(String(255), nullable=True)
    
    # Human Impact Information
    people_affected = Column(Integer, default=0, nullable=False)
    people_trapped = Column(Integer, default=0, nullable=False)
    reporter_safety_status = Column(String(30), default="UNKNOWN")  # SAFE, AT_RISK, TRAPPED, UNKNOWN
    
    # Ingestion Source & Status
    submission_source = Column(String(30), default="APP")  # APP, TWILIO_VOICE, WEB, DISPATCH
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(30), default="SUBMITTED", index=True)  # SUBMITTED, QUEUED, LINKED, REVIEWED, RESOLVED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    reporter = relationship("User", back_populates="reports", foreign_keys=[reporter_id])
    incident = relationship("Incident", back_populates="reports", foreign_keys=[incident_id])
    media_items = relationship("Media", back_populates="report", cascade="all, delete-orphan")
    incident_links = relationship("IncidentReportLink", back_populates="report", cascade="all, delete-orphan")
    ai_analyses = relationship("AIAnalysis", back_populates="report", cascade="all, delete-orphan")
