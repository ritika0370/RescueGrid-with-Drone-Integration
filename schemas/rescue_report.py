"""
Rescue Intelligence Report Schemas (Section 13).
Structured JSON report specification with all 9 mandated sections.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class IncidentIdentificationSection(BaseModel):
    incident_id: str
    emergency_category: str
    first_reported_time: datetime
    last_updated_time: datetime
    current_status: str
    assigned_department: Optional[str] = None


class ExecutiveSummarySection(BaseModel):
    short_description: str
    current_situation: str
    priority_level: str
    urgency_statement: str


class CitizenReportsSection(BaseModel):
    total_linked_reports: int
    individual_report_locations: List[Dict[str, Any]] = []
    citizen_provided_descriptions: List[str] = []
    total_people_reported_affected: int
    total_people_reported_trapped: int
    total_people_reported_injured: int


class GeographicInformationSection(BaseModel):
    incident_area_description: str
    affected_locations: List[Dict[str, Any]] = []
    survey_boundary_polygon: Optional[List[List[float]]] = None
    critical_coordinates: List[Dict[str, Any]] = []


class DroneSurveyFindingsSection(BaseModel):
    missions_count: int
    assigned_drones_and_pilots: List[Dict[str, Any]] = []
    survey_timeframes: List[Dict[str, Any]] = []
    scanned_areas: List[Dict[str, Any]] = []
    raw_observations: List[Dict[str, Any]] = []
    possible_human_sightings: List[Dict[str, Any]] = []
    damage_and_hazards: List[Dict[str, Any]] = []
    photos_and_videos_count: int


class AIAnalysisSection(BaseModel):
    emergency_summary: str
    risk_and_priority_assessment: str
    possible_rescue_priorities: List[str] = []
    uncertainties: List[str] = []
    supporting_evidence: List[Dict[str, Any]] = []
    confidence_score: float


class SuggestedRescuePlanningSection(BaseModel):
    possible_access_routes: List[str] = []
    potentially_affected_areas: List[str] = []
    possible_equipment_requirements: List[str] = []
    areas_requiring_ground_verification: List[str] = []
    suggested_next_steps_for_responders: List[str] = []


class EvidenceAndAuditTrailSection(BaseModel):
    source_report_ids: List[str] = []
    media_ids: List[str] = []
    observation_ids: List[str] = []
    timestamps: Dict[str, Any] = {}
    analysis_timestamps: List[datetime] = []
    officer_review_history: List[Dict[str, Any]] = []


class RescueIntelligenceReport(BaseModel):
    report_title: str = "OFFICIAL RESCUE INTELLIGENCE REPORT"
    generated_at: datetime
    
    # 9 Mandated Sections
    section_1_incident_identification: IncidentIdentificationSection
    section_2_executive_summary: ExecutiveSummarySection
    section_3_citizen_reports: CitizenReportsSection
    section_4_geographic_information: GeographicInformationSection
    section_5_drone_survey_findings: DroneSurveyFindingsSection
    section_6_ai_analysis: AIAnalysisSection
    section_7_suggested_rescue_planning: SuggestedRescuePlanningSection
    section_8_evidence_and_audit_trail: EvidenceAndAuditTrailSection
    section_9_disclaimer: str = (
        "IMPORTANT DISCLAIMER: This rescue intelligence report combines citizen emergency reports, "
        "manual drone pilot findings, and AI decision-support analysis. AI analysis is strictly advisory. "
        "Suggested routes, hazards, and equipment must be verified in the field by qualified incident commanders "
        "and emergency responders. No unverified AI detection represents a confirmed rescue fact."
    )
