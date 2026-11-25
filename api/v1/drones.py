"""
Drone Station and Drone Fleet Registry API.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_officer
from app.models.drone import Drone, DroneStation
from app.schemas.drone import (
    DroneCreateRequest,
    DroneResponse,
    DroneStationResponse,
    DroneTelemetryRequest,
    DroneUpdateRequest,
)
from app.services.drone_service import DroneService

router = APIRouter(prefix="/drones", tags=["Drones & Stations"])


@router.get("/stations", response_model=List[DroneStationResponse])
async def list_drone_stations(db: AsyncSession = Depends(get_db)):
    """List all drone deployment stations."""
    res = await db.execute(select(DroneStation).order_by(DroneStation.name.asc()))
    return res.scalars().all()


@router.get("", response_model=List[DroneResponse])
async def list_drones(
    status_filter: Optional[str] = Query(None, alias="status"),
    station_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List drones with status and station filtering."""
    query = select(Drone).order_by(Drone.battery_percentage.desc())
    if status_filter:
        query = query.where(Drone.availability_status == status_filter)
    if station_id:
        query = query.where(Drone.station_id == station_id)
    res = await db.execute(query)
    return res.scalars().all()


@router.post("", response_model=DroneResponse, status_code=status.HTTP_201_CREATED)
async def register_drone(
    req: DroneCreateRequest,
    db: AsyncSession = Depends(get_db),
    officer=Depends(require_officer),
):
    """Register a new survey drone."""
    return await DroneService.register_drone(db, req)


@router.patch("/{drone_id}", response_model=DroneResponse)
async def update_drone(
    drone_id: str,
    req: DroneUpdateRequest,
    db: AsyncSession = Depends(get_db),
    officer=Depends(require_officer),
):
    """Update drone operational status or assignment."""
    res = await db.execute(select(Drone).where(Drone.id == drone_id))
    drone = res.scalar_one_or_none()
    if not drone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drone not found.")

    if req.station_id:
        drone.station_id = req.station_id
    if req.availability_status:
        drone.availability_status = req.availability_status
    if req.battery_percentage is not None:
        drone.battery_percentage = req.battery_percentage
    if req.latitude is not None:
        drone.latitude = req.latitude
    if req.longitude is not None:
        drone.longitude = req.longitude

    await db.commit()
    await db.refresh(drone)
    return drone


@router.post("/{drone_id}/telemetry", response_model=DroneResponse)
async def submit_drone_telemetry(
    drone_id: str,
    req: DroneTelemetryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest drone telemetry (coordinates, battery %, availability).
    Flags simulated telemetry explicitly.
    """
    drone = await DroneService.update_telemetry(db, drone_id, req)
    if not drone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drone not found.")
    return drone
