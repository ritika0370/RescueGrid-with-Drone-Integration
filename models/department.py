"""
Emergency Department database model.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, JSON, String
from sqlalchemy.orm import relationship
from app.core.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(150), nullable=False, unique=True)
    department_type = Column(String(50), nullable=False, index=True)  # FIRE, POLICE, DISASTER_RESPONSE, MEDICAL, RESCUE
    service_area = Column(JSON, nullable=True)  # Polygon geo coordinates or coverage description
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    contact_information = Column(JSON, nullable=True)  # phone, radio_channel, email, dispatch_head
    status = Column(String(30), default="ACTIVE")  # ACTIVE, BUSY, OFFLINE
    supported_categories = Column(JSON, nullable=False, default=list)  # list of emergency categories
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    users = relationship("User", back_populates="department", foreign_keys="User.department_id")
    incidents = relationship("Incident", back_populates="assigned_department")
    drone_stations = relationship("DroneStation", back_populates="department")
