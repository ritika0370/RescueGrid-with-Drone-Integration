"""
Drone Mission and Job Card Schemas.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class JobCardData(BaseModel):
    mission_id: Optional[str] = None
    incident_id: str
    emergency_category: str
    incident_priority: str
    mission_objective: str
    target_area: str
    survey_boundary_polygon: Optional[List[List[float]]] = None
    important_coordinates: List[Dict[str, Any]] = []
    known_affected_locations: List[Dict[str, Any]] = []
    possible_trapped_person_locations: List[Dict[str, Any]] = []
    hazards_to_avoid_or_investigate: List[str] = []
    areas_requiring_inspection: List[str] = []
    required_observations: List[str] = []
    department_instructions: str
    assigned_drone_id: Optional[str] = None
    assigned_station_id: Optional[str] = None
    assigned_pilot_id: Optional[str] = None
    created_at: Optional[datetime] = None
    status: str = "CREATED"


class MissionCreateRequest(BaseModel):
    incident_id: str
    mission_objective: str
    pilot_id: Optional[str] = None
    drone_id: Optional[str] = None
    department_instructions: Optional[str] = "Conduct low-altitude visual inspection of affected sectors."


class MissionAcceptRequest(BaseModel):
    notes: Optional[str] = None


class MissionRejectRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=3)


class MissionStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="PREPARING, IN_FLIGHT, PAUSED, COMPLETED, CANCELLED")
    notes: Optional[str] = None


class MissionCompleteRequest(BaseModel):
    pilot_notes: Optional[str] = None
    scanned_boundary_geojson: Optional[Dict[str, Any]] = None


class MissionResponse(BaseModel):
    id: str
    incident_id: str
    drone_id: Optional[str] = None
    station_id: Optional[str] = None
    pilot_id: Optional[str] = None
    job_card_json: Dict[str, Any]
    mission_mode: str
    status: str
    rejection_reason: Optional[str] = None
    pilot_notes: Optional[str] = None
    scanned_boundary_geojson: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
