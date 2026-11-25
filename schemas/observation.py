"""
Field Observation and Sighting Schemas.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ObservationCreateRequest(BaseModel):
    source: str = Field(default="PILOT", description="PILOT, SENSOR, AI")
    observation_type: str = Field(
        ...,
        description="HUMAN_SIGHTING, HAZARD, STRUCTURAL_DAMAGE, FLOOD_WATER, ACCESS_ROUTE, OBSTACLE",
    )
    description: str = Field(..., min_length=3)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    verification_status: str = Field(
        default="PILOT_CONFIRMED",
        description="UNVERIFIED_AI, PILOT_CONFIRMED, OFFICER_VERIFIED",
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    media_ids: List[str] = []


class ObservationResponse(BaseModel):
    id: str
    mission_id: str
    incident_id: str
    source: str
    observation_type: str
    description: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    verification_status: str
    confidence: float
    created_at: datetime
    media_ids: List[str] = []

    class Config:
        from_attributes = True
