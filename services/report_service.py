"""
Citizen SOS Emergency Report Ingestion Service (Section 3).
Guarantees immediate acknowledgment of emergency reports while scheduling
multimodal AI processing, media analysis, and incident grouping asynchronously.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.report import Report
from app.schemas.report import ReportAcknowledgeResponse, ReportCreateRequest
from app.services.audit_service import AuditService
from app.services.grouping_service import IncidentGroupingService
from app.services.ai_service import AIEmergencyAnalysisEngine
from app.models.ai_analysis import AIAnalysis
from app.core.events import event_manager


class ReportService:
    @classmethod
    async def ingest_report(
        cls,
        db: AsyncSession,
        request: ReportCreateRequest,
    ) -> ReportAcknowledgeResponse:
        """
        Store SOS report synchronously for zero-delay persistence,
        then initiate async clustering and analysis pipeline.
        """
        report = Report(
            reporter_id=request.reporter_id,
            reporter_phone=request.reporter_phone,
            reporter_name=request.reporter_name,
            emergency_category=request.emergency_category.value if hasattr(request.emergency_category, "value") else str(request.emergency_category),
            description=request.description,
            latitude=request.latitude,
            longitude=request.longitude,
            location_accuracy=request.location_accuracy,
            manually_entered_location=request.manually_entered_location,
            address_or_landmark=request.address_or_landmark,
            people_affected=request.people_affected,
            people_trapped=request.people_trapped,
            reporter_safety_status=request.reporter_safety_status.value if hasattr(request.reporter_safety_status, "value") else str(request.reporter_safety_status),
            submission_source=request.submission_source,
            status="SUBMITTED",
            created_at=datetime.now(timezone.utc),
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)

        # Audit log for non-repudiation
        await AuditService.log_action(
            db,
            action="REPORT_SUBMITTED",
            entity_type="REPORT",
            entity_id=report.id,
            user_id=report.reporter_id,
            details={
                "category": report.emergency_category,
                "lat": report.latitude,
                "lon": report.longitude,
                "source": report.submission_source,
            },
        )

        # Broadcast live SOS arrival to monitoring dashboards
        await event_manager.broadcast_global(
            "NEW_REPORT_ARRIVED",
            {
                "report_id": report.id,
                "category": report.emergency_category,
                "latitude": report.latitude,
                "longitude": report.longitude,
                "description": report.description[:100],
                "trapped": report.people_trapped,
            },
        )

        # Return immediate acknowledgment
        return ReportAcknowledgeResponse(
            report_id=report.id,
            submission_timestamp=report.created_at,
            initial_status=report.status,
            incident_id=report.incident_id,
            confirmation="Emergency report received and logged immediately. Responders alerted.",
        )

    @classmethod
    async def process_report_pipeline(cls, db: AsyncSession, report_id: str) -> None:
        """
        Asynchronous processing pipeline:
        1. Run NLP emergency analysis
        2. Evaluate incident matching and link to existing or new incident
        3. Trigger combined incident situation update
        """
        from sqlalchemy import select
        res = await db.execute(select(Report).where(Report.id == report_id))
        report = res.scalar_one_or_none()
        if not report:
            return

        # 1. NLP Emergency Text Analysis
        text_intel = AIEmergencyAnalysisEngine.analyze_text(report.description, report.emergency_category)
        analysis_record = AIAnalysis(
            report_id=report.id,
            source_type="REPORT",
            source_id=report.id,
            analysis_type="TEXT",
            result_json=text_intel,
            confidence=0.90,
            model_version="TextNLP-Emergency-v1",
        )
        db.add(analysis_record)
        await db.commit()

        # 2. Grouping Engine Evaluation
        incident = await IncidentGroupingService.process_report_grouping(db, report)

        # 3. Update Incident Combined Analysis
        rep_res = await db.execute(select(Report).where(Report.incident_id == incident.id))
        all_linked_reports = rep_res.scalars().all()
        combined_intel = AIEmergencyAnalysisEngine.combine_incident_reports(incident, all_linked_reports)

        comb_analysis = AIAnalysis(
            incident_id=incident.id,
            source_type="INCIDENT",
            source_id=incident.id,
            analysis_type="COMBINED_INCIDENT",
            result_json=combined_intel,
            confidence=combined_intel["confidence"],
            model_version="IncidentSynthesizer-v1",
        )
        db.add(comb_analysis)
        
        # Update incident priority based on combined evaluation if not manually overridden
        if not incident.priority_overridden:
            incident.priority = combined_intel["recommended_priority"]
            incident.priority_reason = combined_intel["priority_rationale"]

        await db.commit()
