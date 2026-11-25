"""
Incident and Grouping schemas.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IncidentReportLinkResponse(BaseModel):
    id: str
    incident_id: str
    report_id: str
    match_confidence: float
    match_reasons: Optional[Dict[str, Any]] = None
    link_status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class IncidentResponse(BaseModel):
    id: str
    emergency_category: str
    summary: str
    priority: str
    priority_reason: Optional[str] = None
    priority_overridden: bool = False
    priority_override_reason: Optional[str] = None
    priority_override_by: Optional[str] = None
    confidence: float
    affected_area: Optional[Dict[str, Any]] = None
    primary_latitude: Optional[float] = None
    primary_longitude: Optional[float] = None
    assigned_department_id: Optional[str] = None
    estimated_affected_people: int
    estimated_trapped_people: int
    status: str
    first_reported_at: datetime
    last_reported_at: datetime
    created_at: datetime
    updated_at: datetime
    linked_reports_count: Optional[int] = 0

    class Config:
        from_attributes = True


class IncidentUpdateRequest(BaseModel):
    summary: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    priority_override_reason: Optional[str] = None
    assigned_department_id: Optional[str] = None


class IncidentReviewLinkRequest(BaseModel):
    link_id: str
    action: str = Field(..., description="CONFIRM or REJECT")
    notes: Optional[str] = None


class IncidentMergeRequest(BaseModel):
    source_incident_id: str = Field(..., description="Incident to merge from and close")
    target_incident_id: str = Field(..., description="Target incident to merge reports into")
    reason: str = Field(..., min_length=3)


class IncidentSplitRequest(BaseModel):
    report_ids: List[str] = Field(..., min_items=1, description="Reports to split out")
    new_incident_summary: str = Field(..., min_length=3)
    reason: str = Field(..., min_length=3)


class IncidentAssignDepartmentRequest(BaseModel):
    department_id: str
    notes: Optional[str] = None
