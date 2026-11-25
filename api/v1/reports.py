"""
Citizen Emergency SOS Report Ingestion and Updates API.
"""
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import get_current_user, get_db, get_optional_user
from app.models.media import Media
from app.models.report import Report
from app.models.user import User
from app.schemas.report import (
    MediaResponse,
    ReportAcknowledgeResponse,
    ReportCreateRequest,
    ReportResponse,
    ReportUpdateRequest,
)
from app.services.media_service import MediaService
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Citizen Reports"])


@router.post("", response_model=ReportAcknowledgeResponse, status_code=status.HTTP_201_CREATED)
async def submit_report(
    req: ReportCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    optional_user: Optional[User] = Depends(get_optional_user),
):
    """
    Ingest a new citizen SOS emergency report.
    Guarantees immediate acknowledgment without waiting for AI inference.
    Schedules asynchronous NLP analysis and multi-factor grouping.
    """
    if optional_user and not req.reporter_id:
        req.reporter_id = optional_user.id
        if not req.reporter_name:
            req.reporter_name = optional_user.name
        if not req.reporter_phone:
            req.reporter_phone = optional_user.phone

    ack = await ReportService.ingest_report(db, req)

    # Trigger asynchronous processing pipeline
    background_tasks.add_task(ReportService.process_report_pipeline, db, ack.report_id)

    return ack


@router.get("/my", response_model=List[ReportResponse])
async def get_my_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all emergency reports submitted by the authenticated citizen."""
    res = await db.execute(
        select(Report)
        .options(selectinload(Report.media_items))
        .where(Report.reporter_id == current_user.id)
        .order_by(Report.created_at.desc())
    )
    return res.scalars().all()


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report_by_id(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full details of an independent citizen report."""
    res = await db.execute(
        select(Report)
        .options(selectinload(Report.media_items))
        .where(Report.id == report_id)
    )
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return report


@router.post("/{report_id}/media", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
async def upload_report_media(
    report_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload media (image, audio recording, video) attached to a report.
    Validates file, computes SHA-256 hash, generates thumbnails, and triggers STT/Vision.
    """
    rep_res = await db.execute(select(Report).where(Report.id == report_id))
    report = rep_res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    content = await file.read()
    try:
        media = await MediaService.upload_and_process_media(
            db=db,
            filename=file.filename or "uploaded_media",
            content=content,
            report_id=report.id,
        )
        return media
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{report_id}/updates", response_model=ReportResponse)
async def update_report(
    report_id: str,
    req: ReportUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Provide updated situation details for an existing report."""
    res = await db.execute(select(Report).where(Report.id == report_id))
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    if req.description:
        report.description += f" [UPDATE]: {req.description}"
    if req.people_affected is not None:
        report.people_affected = req.people_affected
    if req.people_trapped is not None:
        report.people_trapped = req.people_trapped
    if req.reporter_safety_status is not None:
        report.reporter_safety_status = req.reporter_safety_status.value
    if req.address_or_landmark:
        report.address_or_landmark = req.address_or_landmark

    await db.commit()
    await db.refresh(report)
    return report
