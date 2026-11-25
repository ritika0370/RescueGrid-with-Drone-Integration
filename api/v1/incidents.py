"""
Incident Management, Grouping Review, and Operations API.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_officer
from app.models.incident import Incident, IncidentReportLink
from app.models.report import Report
from app.models.user import User
from app.schemas.incident import (
    IncidentAssignDepartmentRequest,
    IncidentMergeRequest,
    IncidentReportLinkResponse,
    IncidentResponse,
    IncidentReviewLinkRequest,
    IncidentSplitRequest,
    IncidentUpdateRequest,
)
from app.schemas.report import ReportResponse
from app.services.audit_service import AuditService
from app.services.routing_service import DepartmentRoutingService
from app.core.events import event_manager

router = APIRouter(prefix="/incidents", tags=["Incidents & Grouping"])


@router.get("", response_model=List[IncidentResponse])
async def list_incidents(
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = None,
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List disaster incidents with optional status, category, and priority filters."""
    query = select(Incident).order_by(Incident.last_reported_at.desc())
    if status_filter:
        query = query.where(Incident.status == status_filter)
    if category:
        query = query.where(Incident.emergency_category == category)
    if priority:
        query = query.where(Incident.priority == priority)

    res = await db.execute(query)
    incidents = res.scalars().all()
    
    # Attach report count
    output = []
    for inc in incidents:
        rep_count_res = await db.execute(select(Report.id).where(Report.incident_id == inc.id))
        count = len(rep_count_res.scalars().all())
        inc_dict = IncidentResponse.model_validate(inc)
        inc_dict.linked_reports_count = count
        output.append(inc_dict)

    return output


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve full incident details."""
    res = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = res.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")
    
    rep_count_res = await db.execute(select(Report.id).where(Report.incident_id == incident.id))
    count = len(rep_count_res.scalars().all())
    inc_resp = IncidentResponse.model_validate(incident)
    inc_resp.linked_reports_count = count
    return inc_resp


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: str,
    req: IncidentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    officer: User = Depends(require_officer),
):
    """
    Update incident summary, status, or override priority.
    Maintains full audit logging of human overrides.
    """
    res = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = res.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    if req.summary:
        incident.summary = req.summary
    if req.status:
        incident.status = req.status
    if req.assigned_department_id:
        incident.assigned_department_id = req.assigned_department_id

    # Human Priority Override
    if req.priority and req.priority != incident.priority:
        old_priority = incident.priority
        incident.priority = req.priority
        incident.priority_overridden = True
        incident.priority_override_reason = req.priority_override_reason or "Manual officer override"
        incident.priority_override_by = officer.id

        await AuditService.log_action(
            db,
            action="INCIDENT_PRIORITY_OVERRIDDEN",
            entity_type="INCIDENT",
            entity_id=incident.id,
            user_id=officer.id,
            details={
                "old_priority": old_priority,
                "new_priority": req.priority,
                "reason": req.priority_override_reason,
            },
        )
        await event_manager.broadcast_incident(
            incident.id,
            "INCIDENT_PRIORITY_CHANGED",
            {"incident_id": incident.id, "priority": req.priority, "overridden_by": officer.name},
        )

    await db.commit()
    await db.refresh(incident)
    return incident


@router.get("/{incident_id}/reports", response_model=List[ReportResponse])
async def get_incident_reports(incident_id: str, db: AsyncSession = Depends(get_db)):
    """List all independent citizen reports linked to this incident."""
    res = await db.execute(select(Report).where(Report.incident_id == incident_id))
    return res.scalars().all()


@router.post("/{incident_id}/review", response_model=IncidentReportLinkResponse)
async def review_incident_link(
    incident_id: str,
    req: IncidentReviewLinkRequest,
    db: AsyncSession = Depends(get_db),
    officer: User = Depends(require_officer),
):
    """
    Authorised officer action: Confirm or Reject a candidate report grouping link.
    """
    res = await db.execute(select(IncidentReportLink).where(IncidentReportLink.id == req.link_id))
    link = res.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found.")

    action = req.action.upper()
    if action not in ["CONFIRM", "REJECT"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action must be CONFIRM or REJECT.")

    link.link_status = "CONFIRMED" if action == "CONFIRM" else "REJECTED"
    link.reviewed_by = officer.id
    from datetime import datetime, timezone
    link.reviewed_at = datetime.now(timezone.utc)
    link.notes = req.notes

    # Update report link if confirmed
    if action == "CONFIRM":
        rep_res = await db.execute(select(Report).where(Report.id == link.report_id))
        report = rep_res.scalar_one_or_none()
        if report:
            report.incident_id = incident_id
            report.status = "LINKED"

    await db.commit()
    await db.refresh(link)

    await AuditService.log_action(
        db,
        action=f"REPORT_LINK_{action}ED",
        entity_type="INCIDENT_REPORT_LINK",
        entity_id=link.id,
        user_id=officer.id,
        details={"incident_id": incident_id, "report_id": link.report_id, "notes": req.notes},
    )
    return link


@router.post("/{incident_id}/merge", response_model=IncidentResponse)
async def merge_incidents(
    incident_id: str,
    req: IncidentMergeRequest,
    db: AsyncSession = Depends(get_db),
    officer: User = Depends(require_officer),
):
    """
    Merge source incident reports into target incident, then close source incident.
    """
    t_res = await db.execute(select(Incident).where(Incident.id == req.target_incident_id))
    target = t_res.scalar_one_or_none()
    s_res = await db.execute(select(Incident).where(Incident.id == req.source_incident_id))
    source = s_res.scalar_one_or_none()

    if not target or not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target or source incident not found.")

    # Move reports to target
    rep_res = await db.execute(select(Report).where(Report.incident_id == source.id))
    source_reports = rep_res.scalars().all()
    for r in source_reports:
        r.incident_id = target.id

    target.estimated_affected_people += source.estimated_affected_people
    target.estimated_trapped_people += source.estimated_trapped_people
    source.status = "CLOSED"
    source.summary += f" [MERGED INTO {target.id}]: {req.reason}"

    await db.commit()
    await db.refresh(target)

    await AuditService.log_action(
        db,
        action="INCIDENTS_MERGED",
        entity_type="INCIDENT",
        entity_id=target.id,
        user_id=officer.id,
        details={"source_incident_id": source.id, "reason": req.reason, "reports_moved": len(source_reports)},
    )
    return target


@router.post("/{incident_id}/split", response_model=IncidentResponse)
async def split_incident(
    incident_id: str,
    req: IncidentSplitRequest,
    db: AsyncSession = Depends(get_db),
    officer: User = Depends(require_officer),
):
    """
    Split specified reports out of an incident into a brand-new separate incident.
    """
    res = await db.execute(select(Incident).where(Incident.id == incident_id))
    parent_incident = res.scalar_one_or_none()
    if not parent_incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    rep_res = await db.execute(select(Report).where(Report.id.in_(req.report_ids)))
    reports_to_split = rep_res.scalars().all()
    if not reports_to_split:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No matching reports found to split.")

    from datetime import datetime, timezone
    new_inc = Incident(
        emergency_category=reports_to_split[0].emergency_category,
        summary=req.new_incident_summary,
        priority=parent_incident.priority,
        confidence=0.85,
        primary_latitude=reports_to_split[0].latitude,
        primary_longitude=reports_to_split[0].longitude,
        status="UNDER_REVIEW",
        first_reported_at=reports_to_split[0].created_at,
        last_reported_at=datetime.now(timezone.utc),
    )
    db.add(new_inc)
    await db.commit()
    await db.refresh(new_inc)

    for r in reports_to_split:
        r.incident_id = new_inc.id

    await db.commit()

    await AuditService.log_action(
        db,
        action="INCIDENT_SPLIT",
        entity_type="INCIDENT",
        entity_id=new_inc.id,
        user_id=officer.id,
        details={"parent_incident_id": parent_incident.id, "reason": req.reason, "reports_split": len(reports_to_split)},
    )
    return new_inc


@router.post("/{incident_id}/assign-department", response_model=IncidentResponse)
async def assign_department(
    incident_id: str,
    req: IncidentAssignDepartmentRequest,
    db: AsyncSession = Depends(get_db),
    officer: User = Depends(require_officer),
):
    """Assign an incident to an authorized emergency department."""
    res = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = res.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    incident.assigned_department_id = req.department_id
    incident.status = "UNDER_REVIEW"
    await db.commit()
    await db.refresh(incident)

    await DepartmentRoutingService.route_and_assign_incident(db, incident, officer_user_id=officer.id)
    return incident
