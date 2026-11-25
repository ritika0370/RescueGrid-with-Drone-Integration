"""
Drone Station and Drone Registry Service (Section 9).
Manages drone fleets, health telemetry, and station availability.
Explicitly flags simulated telemetry per safety requirements.
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.drone import Drone, DroneStation
from app.schemas.drone import DroneCreateRequest, DroneTelemetryRequest
from app.services.audit_service import AuditService


class DroneService:
    @classmethod
    async def create_station(
        cls,
        db: AsyncSession,
        name: str,
        latitude: float,
        longitude: float,
        department_id: Optional[str] = None,
    ) -> DroneStation:
        station = DroneStation(
            name=name,
            department_id=department_id,
            latitude=latitude,
            longitude=longitude,
            status="OPERATIONAL",
        )
        db.add(station)
        await db.commit()
        await db.refresh(station)
        return station

    @classmethod
    async def register_drone(cls, db: AsyncSession, req: DroneCreateRequest) -> Drone:
        drone = Drone(
            model=req.model,
            station_id=req.station_id,
            latitude=req.latitude,
            longitude=req.longitude,
            battery_percentage=req.battery_percentage,
            availability_status="AVAILABLE",
            max_range_km=req.max_range_km,
            max_flight_time_min=req.max_flight_time_min,
            is_simulated=True,
            last_telemetry_at=datetime.now(timezone.utc),
        )
        db.add(drone)
        await db.commit()
        await db.refresh(drone)
        return drone

    @classmethod
    async def update_telemetry(
        cls,
        db: AsyncSession,
        drone_id: str,
        req: DroneTelemetryRequest,
    ) -> Optional[Drone]:
        res = await db.execute(select(Drone).where(Drone.id == drone_id))
        drone = res.scalar_one_or_none()
        if not drone:
            return None

        drone.latitude = req.latitude
        drone.longitude = req.longitude
        drone.battery_percentage = req.battery_percentage
        drone.availability_status = req.availability_status
        drone.is_simulated = req.is_simulated
        drone.last_telemetry_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(drone)

        await AuditService.log_action(
            db,
            action="DRONE_TELEMETRY_UPDATED",
            entity_type="DRONE",
            entity_id=drone.id,
            details={
                "lat": drone.latitude,
                "lon": drone.longitude,
                "battery": drone.battery_percentage,
                "status": drone.availability_status,
                "is_simulated": drone.is_simulated,
            },
        )
        return drone
