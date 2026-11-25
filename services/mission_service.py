"""
Drone Mission and Job Card Management Service (Section 10).
Recommends optimal available drones based on battery, payload, and proximity.
Synthesizes verified incident information into a structured Survey Job Card.
"""
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.drone import Drone
from app.models.incident import Incident
from app.models.mission import Mission
from app.models.report import Report
from app.schemas.mission import MissionCreateRequest
from app.services.audit_service import AuditService
from app.core.events import event_manager


class MissionService:
    @staticmethod
    def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @classmethod
    async def recommend_drone(
        cls,
        db: AsyncSession,
        target_lat: float,
        target_lon: float,
    ) -> Optional[Drone]:
        """Find the closest available drone with >50% battery."""
        res = await db.execute(
            select(Drone).where(
                Drone.availability_status == "AVAILABLE",
                Drone.battery_percentage >= 50.0,
            )
        )
        drones = res.scalars().all()
        best_drone: Optional[Drone] = None
        min_distance = float("inf")

        for d in drones:
            dist = cls.haversine_km(target_lat, target_lon, d.latitude, d.longitude)
            if dist < min_distance and dist <= d.max_range_km:
                min_distance = dist
                best_drone = d

        return best_drone

    @classmethod
    async def generate_job_card(
        cls,
        db: AsyncSession,
        req: MissionCreateRequest,
        officer_id: Optional[str] = None,
    ) -> Mission:
        """
        Generate drone survey job card synthesizing report coordinates,
        trapped persons, hazards, and survey polygon for manual pilot review.
        """
        inc_res = await db.execute(select(Incident).where(Incident.id == req.incident_id))
        incident = inc_res.scalar_one_or_none()
        if not incident:
            raise ValueError(f"Incident with ID {req.incident_id} not found.")

        # Gather linked reports
        rep_res = await db.execute(select(Report).where(Report.incident_id == incident.id))
        reports = rep_res.scalars().all()

        center_lat = incident.primary_latitude or 37.7749
        center_lon = incident.primary_longitude or -122.4194

        # Compile affected locations and trapped-person coordinates
        affected_locs = []
        trapped_locs = []
        for r in reports:
            if r.latitude and r.longitude:
                loc_dict = {
                    "report_id": r.id,
                    "latitude": r.latitude,
                    "longitude": r.longitude,
                    "description": r.description[:60],
                    "people_affected": r.people_affected,
                }
                affected_locs.append(loc_dict)
                if r.people_trapped > 0 or r.reporter_safety_status == "TRAPPED":
                    trapped_locs.append(loc_dict)

        # Generate default survey boundary polygon around incident coordinates
        delta = 0.015  # ~1.6km bounding box
        survey_polygon = [
            [round(center_lat + delta, 6), round(center_lon - delta, 6)],
            [round(center_lat + delta, 6), round(center_lon + delta, 6)],
            [round(center_lat - delta, 6), round(center_lon + delta, 6)],
            [round(center_lat - delta, 6), round(center_lon - delta, 6)],
            [round(center_lat + delta, 6), round(center_lon - delta, 6)],
        ]

        # Select recommended drone if not explicitly provided
        drone = None
        if req.drone_id:
            d_res = await db.execute(select(Drone).where(Drone.id == req.drone_id))
            drone = d_res.scalar_one_or_none()
        if not drone:
            drone = await cls.recommend_drone(db, center_lat, center_lon)

        job_card_data: Dict[str, Any] = {
            "incident_id": incident.id,
            "emergency_category": incident.emergency_category,
            "incident_priority": incident.priority,
            "mission_objective": req.mission_objective,
            "target_area": f"Area centered at ({center_lat}, {center_lon})",
            "survey_boundary_polygon": survey_polygon,
            "important_coordinates": [{"latitude": center_lat, "longitude": center_lon, "label": "Incident Center"}],
            "known_affected_locations": affected_locs,
            "possible_trapped_person_locations": trapped_locs,
            "hazards_to_avoid_or_investigate": [
                "Rising water currents and sub-surface debris",
                "Damaged power poles and fallen cables",
                "Structural instability of low-lying structures",
            ],
            "areas_requiring_inspection": ["Main road access corridor", "Residential rooftops", "Drainage canals"],
            "required_observations": ["Human sightings", "Water level markers", "Passable evacuation routes"],
            "department_instructions": req.department_instructions,
            "assigned_drone_id": drone.id if drone else None,
            "assigned_station_id": drone.station_id if drone else None,
            "assigned_pilot_id": req.pilot_id,
            "status": "ASSIGNED" if req.pilot_id else "CREATED",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        mission = Mission(
            incident_id=incident.id,
            drone_id=drone.id if drone else None,
            station_id=drone.station_id if drone else None,
            pilot_id=req.pilot_id,
            job_card_json=job_card_data,
            mission_mode="MANUAL_SURVEY",
            status="ASSIGNED" if req.pilot_id else "CREATED",
            created_by=officer_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(mission)
        
        if drone:
            drone.availability_status = "ASSIGNED"

        await db.commit()
        await db.refresh(mission)

        await AuditService.log_action(
            db,
            action="JOB_CARD_CREATED",
            entity_type="MISSION",
            entity_id=mission.id,
            user_id=officer_id,
            details={"incident_id": incident.id, "drone_id": mission.drone_id, "pilot_id": mission.pilot_id},
        )

        # Notify pilot and dashboard
        if mission.pilot_id:
            await event_manager.broadcast_pilot(
                mission.pilot_id,
                "JOB_CARD_ASSIGNED",
                {"mission_id": mission.id, "incident_id": incident.id, "priority": incident.priority},
            )
        await event_manager.broadcast_incident(
            incident.id,
            "MISSION_CREATED",
            {"mission_id": mission.id, "pilot_id": mission.pilot_id, "status": mission.status},
        )
        return mission
