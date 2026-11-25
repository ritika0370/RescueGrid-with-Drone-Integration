"""
Incident and Incident-Report Grouping Link database models.
Represents grouped real-world emergencies while preserving all citizen reports.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    emergency_category = Column(String(50), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    
    # Priority Assessment (P1 - P4)
    priority = Column(String(10), default="P3", index=True)  # P1, P2, P3, P4
    priority_reason = Column(Text, nullable=True)
    priority_overridden = Column(Boolean, default=False)
    priority_override_reason = Column(Text, nullable=True)
    priority_override_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # AI Confidence and Geographic Bounds
    confidence = Column(Float, default=0.5, nullable=False)
    affected_area = Column(JSON, nullable=True)  # Polygon geo coordinates or bounding box
    primary_latitude = Column(Float, nullable=True)
    primary_longitude = Column(Float, nullable=True)
    
    # Department Assignment
    assigned_department_id = Column(String(36), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Casualty & Rescue Estimates
    estimated_affected_people = Column(Integer, default=0, nullable=False)
    estimated_trapped_people = Column(Integer, default=0, nullable=False)
    
    # Lifecycle Status
    status = Column(String(30), default="PROVISIONAL", index=True)  # PROVISIONAL, UNDER_REVIEW, ACTIVE, CONTAINED, RESOLVED, CLOSED
    first_reported_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_reported_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    assigned_department = relationship("Department", back_populates="incidents", foreign_keys=[assigned_department_id])
    reports = relationship("Report", back_populates="incident", foreign_keys="Report.incident_id")
    report_links = relationship("IncidentReportLink", back_populates="incident", cascade="all, delete-orphan")
    ai_analyses = relationship("AIAnalysis", back_populates="incident", cascade="all, delete-orphan")
    missions = relationship("Mission", back_populates="incident", cascade="all, delete-orphan")
    observations = relationship("Observation", back_populates="incident", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="incident", cascade="all, delete-orphan")


class IncidentReportLink(Base):
    __tablename__ = "incident_report_links"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    match_confidence = Column(Float, nullable=False)
    match_reasons = Column(JSON, nullable=True)  # Breakdown of spatial, temporal, category, text similarity
    link_status = Column(String(30), default="SUGGESTED", index=True)  # SUGGESTED, CONFIRMED, REJECTED, MERGED
    reviewed_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    incident = relationship("Incident", back_populates="report_links")
    report = relationship("Report", back_populates="incident_links")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
