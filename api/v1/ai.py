"""
AI Emergency Analysis API Endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_officer
from app.models.ai_analysis import AIAnalysis
from app.models.incident import Incident
from app.models.report import Report
from app.schemas.ai import (
    AIAnalysisRecordResponse,
    IncidentCombinedAIAnalysisResponse,
    ReportAIAnalysisResponse,
)
from app.services.ai_service import AIEmergencyAnalysisEngine
from app.services.priority_service import PriorityAssessmentService

router = APIRouter(prefix="/ai", tags=["AI Analysis Engine"])


@router.post("/analyze-report/{report_id}", response_model=ReportAIAnalysisResponse)
async def analyze_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    officer=Depends(require_officer),
):
    """Run text and multimodal AI analysis on a single report."""
    res = await db.execute(select(Report).where(Report.id == report_id))
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    text_intel = AIEmergencyAnalysisEngine.analyze_text(report.description, report.emergency_category)
    priority_res = PriorityAssessmentService.assess_priority(
        category=report.emergency_category,
        description=report.description,
        people_affected=report.people_affected,
        people_trapped=report.people_trapped,
        safety_status=report.reporter_safety_status,
        hazards=[h["hazard_type"] for h in text_intel["hazards"]],
    )

    return ReportAIAnalysisResponse(
        report_id=report.id,
        emergency_type=report.emergency_category,
        urgency_level=text_intel["urgency_level"],
        extracted_locations=text_intel["extracted_locations"],
        possible_trapped_count=text_intel["possible_trapped_count"],
        possible_injured_count=text_intel["possible_injured_count"],
        detected_hazards=text_intel["hazards"],
        recommended_priority=priority_res["recommended_priority"],
        priority_reason="; ".join(priority_res["reasons"]),
        confidence=priority_res["confidence"],
        citations=text_intel["citations"],
    )


@router.post("/analyze-incident/{incident_id}", response_model=IncidentCombinedAIAnalysisResponse)
async def analyze_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    officer=Depends(require_officer),
):
    """Run combined multi-report synthesis for an incident."""
    inc_res = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = inc_res.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    rep_res = await db.execute(select(Report).where(Report.incident_id == incident.id))
    reports = rep_res.scalars().all()

    combined_intel = AIEmergencyAnalysisEngine.combine_incident_reports(incident, reports)

    # Persist analysis record
    record = AIAnalysis(
        incident_id=incident.id,
        source_type="INCIDENT",
        source_id=incident.id,
        analysis_type="COMBINED_INCIDENT",
        result_json=combined_intel,
        confidence=combined_intel["confidence"],
        model_version="IncidentSynthesizer-v1",
    )
    db.add(record)
    await db.commit()

    return IncidentCombinedAIAnalysisResponse(**combined_intel)


@router.get("/analysis/{analysis_id}", response_model=AIAnalysisRecordResponse)
async def get_analysis_record(analysis_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve an existing stored AI analysis record by ID."""
    res = await db.execute(select(AIAnalysis).where(AIAnalysis.id == analysis_id))
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Analysis record not found.")
    return rec
