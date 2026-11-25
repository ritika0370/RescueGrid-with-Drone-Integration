"""
Emergency Department Schemas.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DepartmentCreateRequest(BaseModel):
    name: str = Field(..., min_length=2)
    department_type: str = Field(..., description="FIRE, POLICE, DISASTER_RESPONSE, MEDICAL, RESCUE")
    service_area: Optional[Dict[str, Any]] = None
    latitude: float
    longitude: float
    contact_information: Optional[Dict[str, Any]] = None
    status: str = "ACTIVE"
    supported_categories: List[str] = []


class DepartmentResponse(BaseModel):
    id: str
    name: str
    department_type: str
    service_area: Optional[Dict[str, Any]] = None
    latitude: float
    longitude: float
    contact_information: Optional[Dict[str, Any]] = None
    status: str
    supported_categories: List[str]
    created_at: datetime

    class Config:
        from_attributes = True
