"""
Drone and Drone Station Schemas.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DroneStationResponse(BaseModel):
    id: str
    name: str
    department_id: Optional[str] = None
    latitude: float
    longitude: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DroneCreateRequest(BaseModel):
    model: str = Field(..., min_length=2)
    station_id: Optional[str] = None
    latitude: float
    longitude: float
    battery_percentage: float = 100.0
    max_range_km: float = 15.0
    max_flight_time_min: int = 35


class DroneUpdateRequest(BaseModel):
    station_id: Optional[str] = None
    availability_status: Optional[str] = None
    battery_percentage: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class DroneTelemetryRequest(BaseModel):
    latitude: float
    longitude: float
    battery_percentage: float = Field(..., ge=0.0, le=100.0)
    availability_status: str
    is_simulated: bool = True  # Must be explicitly true if simulated telemetry


class DroneResponse(BaseModel):
    id: str
    model: str
    station_id: Optional[str] = None
    latitude: float
    longitude: float
    battery_percentage: float
    availability_status: str
    max_range_km: float
    max_flight_time_min: int
    last_telemetry_at: Optional[datetime] = None
    is_simulated: bool
    created_at: datetime

    class Config:
        from_attributes = True
