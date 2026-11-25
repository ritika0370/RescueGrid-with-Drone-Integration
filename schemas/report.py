"""
Citizen SOS Emergency Report schemas.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class EmergencyCategory(str, Enum):
    FIRE = "Fire"
    FLOOD = "Flood"
    EARTHQUAKE = "Earthquake"
    BUILDING_COLLAPSE = "Building collapse"
    ROAD_ACCIDENT = "Road accident"
    MEDICAL_EMERGENCY = "Medical emergency"
    MISSING_OR_TRAPPED_PERSON = "Missing or trapped person"
    INDUSTRIAL_OR_CHEMICAL_INCIDENT = "Industrial or chemical incident"
    OTHER_EMERGENCY = "Other emergency"


class ReporterSafetyStatus(str, Enum):
    SAFE = "SAFE"
    AT_RISK = "AT_RISK"
    TRAPPED = "TRAPPED"
    UNKNOWN = "UNKNOWN"


class MediaResponse(BaseModel):
    id: str
    media_type: str
    original_filename: str
    storage_path: str
    thumbnail_path: Optional[str] = None
    sha256_hash: str
    file_size_bytes: int
    processing_status: str
    transcript: Optional[str] = None
    transcript_confidence: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportCreateRequest(BaseModel):
    reporter_id: Optional[str] = None
    reporter_phone: Optional[str] = None
    reporter_name: Optional[str] = None
    emergency_category: EmergencyCategory
    description: str = Field(..., min_length=3)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    location_accuracy: Optional[float] = None
    manually_entered_location: Optional[str] = None
    address_or_landmark: Optional[str] = None
    people_affected: int = Field(0, ge=0)
    people_trapped: int = Field(0, ge=0)
    reporter_safety_status: ReporterSafetyStatus = ReporterSafetyStatus.UNKNOWN
    submission_source: str = "APP"


class ReportAcknowledgeResponse(BaseModel):
    report_id: str
    submission_timestamp: datetime
    initial_status: str
    incident_id: Optional[str] = None
    confirmation: str = "Emergency report acknowledged and queued for response and AI grouping."


class ReportUpdateRequest(BaseModel):
    description: Optional[str] = None
    people_affected: Optional[int] = None
    people_trapped: Optional[int] = None
    reporter_safety_status: Optional[ReporterSafetyStatus] = None
    address_or_landmark: Optional[str] = None


class ReportResponse(BaseModel):
    id: str
    reporter_id: Optional[str] = None
    reporter_phone: Optional[str] = None
    reporter_name: Optional[str] = None
    emergency_category: str
    description: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_accuracy: Optional[float] = None
    manually_entered_location: Optional[str] = None
    address_or_landmark: Optional[str] = None
    people_affected: int
    people_trapped: int
    reporter_safety_status: str
    submission_source: str
    incident_id: Optional[str] = None
    status: str
    created_at: datetime
    media_items: List[MediaResponse] = []

    class Config:
        from_attributes = True
