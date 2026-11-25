"""
Twilio Inbound Emergency Call Log database model.
Tracks calls from citizens reporting disasters via phone call,
linking their voice recording and transcription directly to an SOS Report.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class TwilioCallLog(Base):
    __tablename__ = "twilio_call_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    call_sid = Column(String(64), unique=True, index=True, nullable=False)
    from_phone = Column(String(30), nullable=False, index=True)
    to_phone = Column(String(30), nullable=False)
    caller_city = Column(String(100), nullable=True)
    caller_state = Column(String(100), nullable=True)
    caller_zip = Column(String(20), nullable=True)
    
    recording_url = Column(String(500), nullable=True)
    recording_duration = Column(Integer, nullable=True)
    transcription_text = Column(Text, nullable=True)
    
    linked_report_id = Column(String(36), ForeignKey("reports.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(30), default="INCOMING", index=True)  # INCOMING, GATHERED, RECORDED, TRANSCRIBED, REPORT_CREATED, FAILED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    report = relationship("Report", foreign_keys=[linked_report_id])
