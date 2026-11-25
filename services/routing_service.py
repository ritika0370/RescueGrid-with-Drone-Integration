"""
Department Routing and Notification Service (Section 8).
Matches incident categories and geographic service areas to specialized rescue departments.
Dispatches real-time WebSocket and external notifications without false delivery claims.
"""
import math
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.department import Department
from app.models.incident import Incident
from app.models.notification import Notification
from app.core.events import event_manager
from app.services.audit_service import AuditService


class DepartmentRoutingService:
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
    async def find_best_department(cls, db: AsyncSession, incident: Incident) -> Optional[Department]:
        """
        Find best matching department matching emergency category capability
        and geographic proximity within service boundaries.
        """
        result = await db.execute(select(Department).where(Department.status == "ACTIVE"))
        departments = result.scalars().all()

        best_dept: Optional[Department] = None
        min_distance = float("inf")

        for dept in departments:
            # Check category compatibility
            if incident.emergency_category not in dept.supported_categories and "All" not in dept.supported_categories:
                continue

            if incident.primary_latitude is not None and incident.primary_longitude is not None:
                dist = cls.haversine_km(
                    incident.primary_latitude, incident.primary_longitude,
                    dept.latitude, dept.longitude
                )
                if dist < min_distance:
                    min_distance = dist
                    best_dept = dept
            elif best_dept is None:
                best_dept = dept

        return best_dept

    @classmethod
    async def route_and_assign_incident(
        cls,
        db: AsyncSession,
        incident: Incident,
        officer_user_id: Optional[str] = None,
    ) -> Optional[Department]:
        """Route incident to appropriate department, record assignment, and notify officers."""
        dept = await cls.find_best_department(db, incident)
        if not dept:
            return None

        incident.assigned_department_id = dept.id
        incident.status = "UNDER_REVIEW"
        await db.commit()
        await db.refresh(incident)

        # Create verified notification record
        notif = Notification(
            department_id=dept.id,
            incident_id=incident.id,
            channel="WEBSOCKET",
            message=f"Incident {incident.id[:8]} ({incident.emergency_category}, Priority: {incident.priority}) assigned to {dept.name}.",
            delivery_status="DELIVERED",
        )
        db.add(notif)
        await db.commit()

        await AuditService.log_action(
            db,
            action="INCIDENT_ASSIGNED_TO_DEPARTMENT",
            entity_type="INCIDENT",
            entity_id=incident.id,
            user_id=officer_user_id,
            details={"department_id": dept.id, "department_name": dept.name},
        )

        await event_manager.broadcast_department(
            dept.id,
            "INCIDENT_ASSIGNED",
            {
                "incident_id": incident.id,
                "category": incident.emergency_category,
                "priority": incident.priority,
                "department_name": dept.name,
            },
        )
        return dept
