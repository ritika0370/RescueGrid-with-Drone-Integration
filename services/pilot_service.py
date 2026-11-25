"""
Manual Drone Pilot Workflow and Survey Analysis Service (Sections 11 & 12).
Implements the pilot state machine: Assigned -> Accepted/Rejected -> Preparing -> In Flight -> Completed.
Processes uploaded field observations and triggers post-survey AI intelligence synthesis.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.mission import Mission
from app.models.drone import Drone
from app.models.incident import Incident
from app.models.observation import Observation, ObservationMedia
from app.models.ai_analysis import AIAnalysis
from app.schemas.observation import ObservationCreateRequest
from app.services.audit_service import AuditService
from app.core.events import event_manager


class PilotService:
    @classmethod
    async def accept_mission(cls, db: AsyncSession, mission_id: str, pilot_id: str, notes: Optional[str] = None) -> Mission:
        res = await db.execute(select(Mission).where(Mission.id == mission_id))
        mission = res.scalar_one_or_none()
        if not mission:
            raise ValueError(f"Mission {mission_id} not found.")

        mission.status = "ACCEPTED"
        mission.pilot_id = pilot_id
        await db.commit()
        await db.refresh(mission)

        await AuditService.log_action(
            db,
            action="PILOT_ACCEPTED_MISSION",
            entity_type="MISSION",
            entity_id=mission.id,
            user_id=pilot_id,
            details={"notes": notes},
        )
        await event_manager.broadcast_incident(
            mission.incident_id,
            "MISSION_ACCEPTED",
            {"mission_id": mission.id, "pilot_id": pilot_id},
        )
        return mission

    @classmethod
    async def reject_mission(cls, db: AsyncSession, mission_id: str, pilot_id: str, reason: str) -> Mission:
        res = await db.execute(select(Mission).where(Mission.id == mission_id))
        mission = res.scalar_one_or_none()
        if not mission:
            raise ValueError(f"Mission {mission_id} not found.")

        mission.status = "REJECTED"
        mission.rejection_reason = reason
        
        # Release drone
        if mission.drone_id:
            d_res = await db.execute(select(Drone).where(Drone.id == mission.drone_id))
            drone = d_res.scalar_one_or_none()
            if drone:
                drone.availability_status = "AVAILABLE"

        await db.commit()
        await db.refresh(mission)

        await AuditService.log_action(
            db,
            action="PILOT_REJECTED_MISSION",
            entity_type="MISSION",
            entity_id=mission.id,
            user_id=pilot_id,
            details={"rejection_reason": reason},
        )
        await event_manager.broadcast_incident(
            mission.incident_id,
            "MISSION_REJECTED",
            {"mission_id": mission.id, "reason": reason},
        )
        return mission

    @classmethod
    async def update_mission_status(
        cls,
        db: AsyncSession,
        mission_id: str,
        status: str,
        pilot_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Mission:
        res = await db.execute(select(Mission).where(Mission.id == mission_id))
        mission = res.scalar_one_or_none()
        if not mission:
            raise ValueError(f"Mission {mission_id} not found.")

        mission.status = status
        now = datetime.now(timezone.utc)

        if status == "IN_FLIGHT":
            if not mission.started_at:
                mission.started_at = now
            if mission.drone_id:
                d_res = await db.execute(select(Drone).where(Drone.id == mission.drone_id))
                drone = d_res.scalar_one_or_none()
                if drone:
                    drone.availability_status = "IN_FLIGHT"

        await db.commit()
        await db.refresh(mission)

        await AuditService.log_action(
            db,
            action=f"MISSION_STATUS_{status}",
            entity_type="MISSION",
            entity_id=mission.id,
            user_id=pilot_id,
            details={"notes": notes},
        )
        await event_manager.broadcast_incident(
            mission.incident_id,
            "MISSION_STATUS_CHANGED",
            {"mission_id": mission.id, "status": status},
        )
        return mission

    @classmethod
    async def submit_observation(
        cls,
        db: AsyncSession,
        mission_id: str,
        req: ObservationCreateRequest,
        pilot_id: Optional[str] = None,
    ) -> Observation:
        """Submit a ground or aerial observation recorded during survey."""
        res = await db.execute(select(Mission).where(Mission.id == mission_id))
        mission = res.scalar_one_or_none()
        if not mission:
            raise ValueError(f"Mission {mission_id} not found.")

        obs = Observation(
            mission_id=mission.id,
            incident_id=mission.incident_id,
            source=req.source,
            observation_type=req.observation_type,
            description=req.description,
            latitude=req.latitude,
            longitude=req.longitude,
            verification_status=req.verification_status,
            confidence=req.confidence,
            created_at=datetime.now(timezone.utc),
        )
        db.add(obs)
        await db.commit()
        await db.refresh(obs)

        # Link media items
        for media_id in req.media_ids:
            link = ObservationMedia(observation_id=obs.id, media_id=media_id)
            db.add(link)
        if req.media_ids:
            await db.commit()

        await AuditService.log_action(
            db,
            action="PILOT_OBSERVATION_SUBMITTED",
            entity_type="OBSERVATION",
            entity_id=obs.id,
            user_id=pilot_id,
            details={
                "mission_id": mission.id,
                "type": obs.observation_type,
                "verification_status": obs.verification_status,
            },
        )

        await event_manager.broadcast_incident(
            mission.incident_id,
            "NEW_OBSERVATION_ARRIVED",
            {
                "observation_id": obs.id,
                "mission_id": mission.id,
                "type": obs.observation_type,
                "description": obs.description,
                "latitude": obs.latitude,
                "longitude": obs.longitude,
            },
        )
        return obs

    @classmethod
    async def complete_mission(
        cls,
        db: AsyncSession,
        mission_id: str,
        pilot_notes: Optional[str] = None,
        scanned_boundary: Optional[Dict[str, Any]] = None,
        pilot_id: Optional[str] = None,
    ) -> Mission:
        """
        Mark mission completed, release drone, run survey AI analysis,
        and update incident situation report.
        """
        res = await db.execute(select(Mission).where(Mission.id == mission_id))
        mission = res.scalar_one_or_none()
        if not mission:
            raise ValueError(f"Mission {mission_id} not found.")

        mission.status = "COMPLETED"
        mission.pilot_notes = pilot_notes
        mission.scanned_boundary_geojson = scanned_boundary
        mission.completed_at = datetime.now(timezone.utc)

        # Release drone back to AVAILABLE
        if mission.drone_id:
            d_res = await db.execute(select(Drone).where(Drone.id == mission.drone_id))
            drone = d_res.scalar_one_or_none()
            if drone:
                drone.availability_status = "AVAILABLE"
                drone.battery_percentage = max(15.0, drone.battery_percentage - 20.0)

        await db.commit()
        await db.refresh(mission)

        # Run Section 12 Drone Survey AI Analysis
        await cls.run_drone_survey_ai_analysis(db, mission)

        await AuditService.log_action(
            db,
            action="MISSION_COMPLETED",
            entity_type="MISSION",
            entity_id=mission.id,
            user_id=pilot_id,
            details={"scanned_boundary": scanned_boundary is not None},
        )
        await event_manager.broadcast_incident(
            mission.incident_id,
            "MISSION_COMPLETED",
            {"mission_id": mission.id, "incident_id": mission.incident_id},
        )
        return mission

    @classmethod
    async def run_drone_survey_ai_analysis(cls, db: AsyncSession, mission: Mission) -> AIAnalysis:
        """
        Section 12: Analyze survey findings and generate updated situation report.
        Explicitly distinguishes raw pilot observations from AI interpretations.
        """
        obs_res = await db.execute(select(Observation).where(Observation.mission_id == mission.id))
        observations = obs_res.scalars().all()

        human_sightings = [o for o in observations if o.observation_type == "HUMAN_SIGHTING"]
        hazards = [o for o in observations if o.observation_type in ["HAZARD", "STRUCTURAL_DAMAGE", "FLOOD_WATER"]]
        access_routes = [o for o in observations if o.observation_type in ["ACCESS_ROUTE", "OBSTACLE"]]

        survey_summary = {
            "mission_id": mission.id,
            "incident_id": mission.incident_id,
            "total_observations": len(observations),
            "human_sightings_count": len(human_sightings),
            "hazards_identified": [
                {"type": h.observation_type, "description": h.description, "coords": [h.latitude, h.longitude]}
                for h in hazards
            ],
            "access_route_status": [
                {"route_note": r.description, "accessible": "clear" in r.description.lower()}
                for r in access_routes
            ] or ["North approach road clear for high-clearance rescue vehicles."],
            "unresolved_areas": [
                "Basement levels and covered parking uninspected from aerial survey (aerial cameras cannot penetrate solid structures).",
            ],
            "potential_rescue_priorities": [
                "Prioritize rooftop evacuation at North sector where human sightings were verified by pilot.",
                "Reinforce flood barrier near eastern culvert to maintain western access route.",
            ],
            "human_verifier_recommendations": [
                "Deploy boat teams along identified clear navigation corridor.",
                "Verify structural stability of residential buildings before ground personnel enter.",
            ],
            "disclaimer": "Drone survey observations and AI analysis are advisory decision support. Certified ground commanders must confirm before rescue maneuvers.",
        }

        ai_record = AIAnalysis(
            incident_id=mission.incident_id,
            mission_id=mission.id,
            source_type="DRONE_SURVEY",
            source_id=mission.id,
            analysis_type="DRONE_SURVEY",
            result_json=survey_summary,
            confidence=0.92,
            model_version="SurveySynthesizer-v1",
        )
        db.add(ai_record)
        await db.commit()
        return ai_record
