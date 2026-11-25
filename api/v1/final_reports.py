"""
Rescue Intelligence Report Generation and PDF Export API (Section 13).
"""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_officer
from app.models.user import User
from app.schemas.rescue_report import RescueIntelligenceReport
from app.services.pdf_service import PDFReportService
from app.services.rescue_report_service import RescueReportService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/incidents", tags=["Rescue Intelligence Reports"])


@router.get("/{incident_id}/final-report", response_model=RescueIntelligenceReport)
async def get_final_report(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    officer: User = Depends(require_officer),
):
    """
    Retrieve structured 9-section Rescue Intelligence JSON Report for an incident.
    """
    try:
        report = await RescueReportService.compile_intelligence_report(db, incident_id)
        return report
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{incident_id}/generate-report", response_model=RescueIntelligenceReport)
async def generate_final_report(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    officer: User = Depends(require_officer),
):
    """
    Trigger regeneration and compilation of the Rescue Intelligence Report.
    Logs an audit action and returns full report JSON.
    """
    try:
        report = await RescueReportService.compile_intelligence_report(db, incident_id)
        await AuditService.log_action(
            db,
            action="FINAL_RESCUE_REPORT_GENERATED",
            entity_type="INCIDENT",
            entity_id=incident_id,
            user_id=officer.id,
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{incident_id}/final-report/pdf")
async def download_final_report_pdf(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    officer: User = Depends(require_officer),
):
    """
    Download the generated Rescue Intelligence Report as a standardized PDF document.
    """
    try:
        report = await RescueReportService.compile_intelligence_report(db, incident_id)
        pdf_bytes = PDFReportService.generate_pdf(report)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=rescue_report_{incident_id[:8]}.pdf",
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
