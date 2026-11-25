"""
Incident Creation and Report Grouping Engine (Section 5).
Multi-factor clustering algorithm combining:
1. Geographic proximity (Haversine formula, adaptive disaster radii)
2. Temporal difference
3. Emergency category compatibility
4. Text description similarity (Jaccard token overlap)
5. Shared landmarks / named location matching
Preserves all individual citizen reports, coordinates, and full auditability.
"""
import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.incident import Incident, IncidentReportLink
from app.models.report import Report
from app.services.ai_service import AIEmergencyAnalysisEngine
from app.services.audit_service import AuditService
from app.core.events import event_manager


class IncidentGroupingService:
    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great-circle distance between two GPS coordinates in kilometers."""
        R = 6371.0  # Earth radius in kilometers
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @staticmethod
    def compute_text_similarity(text1: str, text2: str) -> float:
        """Compute token-based Jaccard similarity between two texts."""
        stopwords = {"the", "a", "an", "is", "in", "at", "and", "or", "of", "to", "for", "on", "with", "there", "are", "we"}
        tokens1 = set(re.findall(r"\w+", text1.lower())) - stopwords
        tokens2 = set(re.findall(r"\w+", text2.lower())) - stopwords
        if not tokens1 or not tokens2:
            return 0.0
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        return len(intersection) / len(union)

    @classmethod
    def calculate_match_confidence(
        cls,
        report: Report,
        incident: Incident,
        incident_reports: List[Report],
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Evaluate multi-factor match between a new report and an existing incident.
        Returns (confidence_score, breakdown_reasons).
        """
        reasons = {}

        # 1. Geographic Proximity
        # Adaptive radius: wide-area events (Flood, Earthquake) have larger footprint (up to 12 km),
        # whereas Fire or Road accidents have tight spatial boundaries (up to 2 km).
        category_max_radius = {
            "Flood": 12.0,
            "Earthquake": 25.0,
            "Fire": 2.0,
            "Building collapse": 3.0,
            "Road accident": 1.5,
            "Medical emergency": 1.5,
            "Industrial or chemical incident": 5.0,
        }.get(report.emergency_category, settings.GROUPING_MAX_DISTANCE_KM)

        min_distance = float("inf")
        if report.latitude is not None and report.longitude is not None:
            # Check distance against primary coordinates of incident
            if incident.primary_latitude is not None and incident.primary_longitude is not None:
                d = cls.haversine_distance_km(
                    report.latitude, report.longitude,
                    incident.primary_latitude, incident.primary_longitude
                )
                min_distance = min(min_distance, d)

            # Check distance against any linked reports in the incident
            for other_r in incident_reports:
                if other_r.latitude is not None and other_r.longitude is not None:
                    d = cls.haversine_distance_km(
                        report.latitude, report.longitude,
                        other_r.latitude, other_r.longitude
                    )
                    min_distance = min(min_distance, d)

        if min_distance <= category_max_radius:
            spatial_score = max(0.0, 1.0 - (min_distance / category_max_radius))
        else:
            spatial_score = 0.0
        reasons["spatial_distance_km"] = round(min_distance, 2) if min_distance != float("inf") else None
        reasons["spatial_score"] = round(spatial_score, 3)

        # 2. Temporal Proximity
        now = report.created_at.replace(tzinfo=timezone.utc if report.created_at.tzinfo is None else report.created_at.tzinfo)
        inc_last = incident.last_reported_at.replace(tzinfo=timezone.utc if incident.last_reported_at.tzinfo is None else incident.last_reported_at.tzinfo)
        hours_diff = abs((now - inc_last).total_seconds()) / 3600.0
        max_hours = settings.GROUPING_TIME_WINDOW_HOURS
        temporal_score = max(0.0, 1.0 - (hours_diff / max_hours)) if hours_diff <= max_hours else 0.0
        reasons["hours_difference"] = round(hours_diff, 2)
        reasons["temporal_score"] = round(temporal_score, 3)

        # 3. Category Match
        if report.emergency_category == incident.emergency_category:
            category_score = 1.0
        elif (
            (report.emergency_category in ["Flood", "Missing or trapped person"] and incident.emergency_category in ["Flood", "Missing or trapped person"])
            or (report.emergency_category in ["Building collapse", "Earthquake"] and incident.emergency_category in ["Building collapse", "Earthquake"])
        ):
            category_score = 0.70  # Co-occurring disaster categories
        else:
            category_score = 0.10
        reasons["category_score"] = round(category_score, 3)

        # 4. Text & Landmark Similarity
        text_sim = cls.compute_text_similarity(report.description, incident.summary)
        # Also check against linked descriptions
        for other_r in incident_reports:
            text_sim = max(text_sim, cls.compute_text_similarity(report.description, other_r.description))

        landmark_match = False
        if report.address_or_landmark and incident.summary:
            landmark_words = set(re.findall(r"\w+", report.address_or_landmark.lower()))
            if any(w in incident.summary.lower() for w in landmark_words if len(w) > 4):
                landmark_match = True

        reasons["text_similarity"] = round(text_sim, 3)
        reasons["shared_landmark_found"] = landmark_match

        # Weighted synthesis
        weighted_score = (
            (spatial_score * 0.35)
            + (temporal_score * 0.20)
            + (category_score * 0.25)
            + (text_sim * 0.15)
            + (0.10 if landmark_match else 0.0)
        )
        total_confidence = min(1.0, max(0.0, weighted_score))
        return round(total_confidence, 3), reasons

    @classmethod
    async def process_report_grouping(cls, db: AsyncSession, report: Report) -> Incident:
        """
        Evaluate candidate incidents for a newly ingested report.
        Outcomes:
        - High-confidence match (>= 0.70): link to existing incident automatically / suggest link.
        - Medium-confidence match (0.35 - 0.69): create link in SUGGESTED status for officer review.
        - Low-confidence match (< 0.35): create a new provisional incident.
        """
        # Fetch active or provisional incidents
        result = await db.execute(
            select(Incident).where(Incident.status.in_(["PROVISIONAL", "UNDER_REVIEW", "ACTIVE"]))
        )
        active_incidents = result.scalars().all()

        best_incident: Optional[Incident] = None
        best_confidence = 0.0
        best_reasons: Dict[str, Any] = {}

        for incident in active_incidents:
            # Load incident reports for deep grouping evaluation
            rep_res = await db.execute(select(Report).where(Report.incident_id == incident.id))
            linked_reps = rep_res.scalars().all()

            confidence, reasons = cls.calculate_match_confidence(report, incident, linked_reps)
            if confidence > best_confidence:
                best_confidence = confidence
                best_incident = incident
                best_reasons = reasons

        # High confidence match: link directly to existing incident
        if best_incident and best_confidence >= settings.GROUPING_HIGH_CONFIDENCE_THRESHOLD:
            report.incident_id = best_incident.id
            report.status = "LINKED"
            
            # Update incident timing and human impact metrics
            best_incident.last_reported_at = report.created_at
            best_incident.estimated_affected_people += report.people_affected
            best_incident.estimated_trapped_people += report.people_trapped

            link = IncidentReportLink(
                incident_id=best_incident.id,
                report_id=report.id,
                match_confidence=best_confidence,
                match_reasons=best_reasons,
                link_status="CONFIRMED",
                notes=f"Auto-grouped by AI Grouping Engine with high confidence ({best_confidence}).",
            )
            db.add(link)
            await db.commit()
            await db.refresh(best_incident)

            await AuditService.log_action(
                db,
                action="REPORT_LINKED_TO_INCIDENT",
                entity_type="INCIDENT",
                entity_id=best_incident.id,
                details={"report_id": report.id, "confidence": best_confidence, "reasons": best_reasons},
            )
            await event_manager.broadcast_incident(
                best_incident.id,
                "REPORT_LINKED",
                {"incident_id": best_incident.id, "report_id": report.id, "confidence": best_confidence},
            )
            return best_incident

        # Medium confidence match: queue link for officer review, create provisional incident or link as SUGGESTED
        elif best_incident and best_confidence >= settings.GROUPING_MEDIUM_CONFIDENCE_THRESHOLD:
            # Create a separate provisional incident, but also record the suggested link to best_incident
            new_incident = await cls._create_provisional_incident(db, report)
            link = IncidentReportLink(
                incident_id=best_incident.id,
                report_id=report.id,
                match_confidence=best_confidence,
                match_reasons=best_reasons,
                link_status="SUGGESTED",
                notes=f"Medium confidence candidate match ({best_confidence}). Awaiting officer review.",
            )
            db.add(link)
            await db.commit()
            await db.refresh(new_incident)

            await AuditService.log_action(
                db,
                action="REPORT_CANDIDATE_LINK_SUGGESTED",
                entity_type="INCIDENT",
                entity_id=best_incident.id,
                details={"report_id": report.id, "confidence": best_confidence, "reasons": best_reasons},
            )
            return new_incident

        # Low confidence match: create a separate provisional incident
        else:
            return await cls._create_provisional_incident(db, report)

    @classmethod
    async def _create_provisional_incident(cls, db: AsyncSession, report: Report) -> Incident:
        """Create a new independent provisional incident for a report."""
        summary = f"{report.emergency_category} reported at {report.address_or_landmark or report.manually_entered_location or 'reported coordinates'}. {report.description[:120]}"
        new_incident = Incident(
            emergency_category=report.emergency_category,
            summary=summary,
            priority="P2" if report.people_trapped > 0 else "P3",
            confidence=0.85,
            primary_latitude=report.latitude,
            primary_longitude=report.longitude,
            estimated_affected_people=report.people_affected,
            estimated_trapped_people=report.people_trapped,
            status="PROVISIONAL",
            first_reported_at=report.created_at,
            last_reported_at=report.created_at,
        )
        db.add(new_incident)
        await db.commit()
        await db.refresh(new_incident)

        report.incident_id = new_incident.id
        report.status = "LINKED"

        link = IncidentReportLink(
            incident_id=new_incident.id,
            report_id=report.id,
            match_confidence=1.0,
            match_reasons={"note": "Initial founding report for incident."},
            link_status="CONFIRMED",
        )
        db.add(link)
        await db.commit()

        await AuditService.log_action(
            db,
            action="INCIDENT_CREATED_PROVISIONAL",
            entity_type="INCIDENT",
            entity_id=new_incident.id,
            details={"founding_report_id": report.id, "category": report.emergency_category},
        )
        await event_manager.broadcast_global(
            "INCIDENT_CREATED",
            {"incident_id": new_incident.id, "category": new_incident.emergency_category, "priority": new_incident.priority},
        )
        return new_incident
