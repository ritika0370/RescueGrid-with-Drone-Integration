"""
Drone Mission and Manual Pilot Operations API.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_officer, require_pilot
from app.models.mission import Mission
from app.models.observation import Observation
from app.models.user import User
from app.schemas.mission import (
    MissionAcceptRequest,
    MissionCompleteRequest,
    MissionCreateRequest,
    MissionRejectRequest,
    MissionResponse,
    MissionStatusUpdateRequest,
)
from app.schemas.observation import ObservationCreateRequest, ObservationResponse
from app.services.mission_service import MissionService
from app.services.pilot_service import PilotService

router = APIRouter(prefix="/missions", tags=["Missions & Pilot Workflow"])


@router.post("", response_model=MissionResponse, status_code=status.HTTP_201_CREATED)
async def create_mission_job_card(
    req: MissionCreateRequest,
    db: AsyncSession = Depends(get_db),
    officer: User = Depends(require_officer),
):
    """
    Generate a new drone survey job card for manual pilot review and assignment.
    Synthesizes coordinates, trapped persons, hazards, and survey polygon.
    """
    try:
        mission = await MissionService.generate_job_card(db, req, officer_id=officer.id)
        return mission
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[MissionResponse])
async def list_missions(
    status_filter: Optional[str] = Query(None, alias="status"),
    incident_id: Optional[str] = None,
    pilot_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List drone survey missions."""
    query = select(Mission).order_by(Mission.created_at.desc())
    if status_filter:
        query = query.where(Mission.status == status_filter)
    if incident_id:
        query = query.where(Mission.incident_id == incident_id)
    if pilot_id:
        query = query.where(Mission.pilot_id == pilot_id)
    res = await db.execute(query)
    return res.scalars().all()


@router.get("/{mission_id}", response_model=MissionResponse)
async def get_mission(mission_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve details and complete job card for a mission."""
    res = await db.execute(select(Mission).where(Mission.id == mission_id))
    mission = res.scalar_one_or_none()
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found.")
    return mission


@router.post("/{mission_id}/accept", response_model=MissionResponse)
async def accept_mission(
    mission_id: str,
    req: MissionAcceptRequest,
    db: AsyncSession = Depends(get_db),
    pilot: User = Depends(require_pilot),
):
    """Pilot operation: Accept assigned job card."""
    try:
        return await PilotService.accept_mission(db, mission_id, pilot.id, req.notes)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{mission_id}/reject", response_model=MissionResponse)
async def reject_mission(
    mission_id: str,
    req: MissionRejectRequest,
    db: AsyncSession = Depends(get_db),
    pilot: User = Depends(require_pilot),
):
    """Pilot operation: Reject assigned job card with recorded reason."""
    try:
        return await PilotService.reject_mission(db, mission_id, pilot.id, req.rejection_reason)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{mission_id}/status", response_model=MissionResponse)
async def update_mission_status(
    mission_id: str,
    req: MissionStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    pilot: User = Depends(require_pilot),
):
    """Pilot operation: Update mission state (PREPARING, IN_FLIGHT, PAUSED, CANCELLED)."""
    try:
        return await PilotService.update_mission_status(db, mission_id, req.status, pilot.id, req.notes)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{mission_id}/observations", response_model=ObservationResponse, status_code=status.HTTP_201_CREATED)
async def submit_observation(
    mission_id: str,
    req: ObservationCreateRequest,
    db: AsyncSession = Depends(get_db),
    pilot: User = Depends(require_pilot),
):
    """Pilot operation: Submit field observation with coordinates and media links."""
    try:
        return await PilotService.submit_observation(db, mission_id, req, pilot.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{mission_id}/complete", response_model=MissionResponse)
async def complete_mission(
    mission_id: str,
    req: MissionCompleteRequest,
    db: AsyncSession = Depends(get_db),
    pilot: User = Depends(require_pilot),
):
    """
    Pilot operation: Mark survey mission complete.
    Triggers automated AI analysis of survey findings and releases assigned drone.
    """
    try:
        return await PilotService.complete_mission(
            db,
            mission_id,
            pilot_notes=req.pilot_notes,
            scanned_boundary=req.scanned_boundary_geojson,
            pilot_id=pilot.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
