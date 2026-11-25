"""
Notification database model.
Tracks outbound notifications to emergency departments, officers, and pilots.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(String(36), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True, index=True)
    
    channel = Column(String(30), default="WEBSOCKET", nullable=False)  # WEBSOCKET, SMS, EMAIL, TWILIO_VOICE
    message = Column(Text, nullable=False)
    delivery_status = Column(String(30), default="DELIVERED", nullable=False)  # PENDING, DELIVERED, FAILED
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    recipient = relationship("User", foreign_keys=[recipient_id])
    department = relationship("Department", foreign_keys=[department_id])
    incident = relationship("Incident", back_populates="notifications")
