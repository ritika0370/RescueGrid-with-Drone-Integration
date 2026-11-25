"""
AI Analysis record database model.
Maintains structured findings, citations to source evidence, confidence levels,
and distinguishes citizen reports from AI detections.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import relationship
from app.core.database import Base


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True, index=True)
    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=True, index=True)
    mission_id = Column(String(36), ForeignKey("missions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    source_type = Column(String(30), nullable=False, index=True)  # REPORT, INCIDENT, MISSION, DRONE_SURVEY
    source_id = Column(String(36), nullable=False)
    analysis_type = Column(String(30), nullable=False, index=True)  # TEXT, AUDIO, VISION, COMBINED_INCIDENT, DRONE_SURVEY
    
    result_json = Column(JSON, nullable=False)
    confidence = Column(Float, default=0.5, nullable=False)
    model_version = Column(String(50), default="1.0.0", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    incident = relationship("Incident", back_populates="ai_analyses")
    report = relationship("Report", back_populates="ai_analyses")
    mission = relationship("Mission", back_populates="ai_analyses")
