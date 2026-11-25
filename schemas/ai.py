"""
AI Emergency Analysis Schemas.
Preserves explicit separation between confirmed statements, detections, and citations.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class HazardDetection(BaseModel):
    hazard_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    confidence: float
    source: str  # CITIZEN_STATEMENT, AI_VISION_DETECTION, SENSOR, PILOT_OBSERVATION


class AIAnalysisRecordResponse(BaseModel):
    id: str
    incident_id: Optional[str] = None
    report_id: Optional[str] = None
    mission_id: Optional[str] = None
    source_type: str
    source_id: str
    analysis_type: str
    result_json: Dict[str, Any]
    confidence: float
    model_version: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReportAIAnalysisResponse(BaseModel):
    report_id: str
    emergency_type: str
    urgency_level: str
    extracted_locations: List[str] = []
    possible_trapped_count: int = 0
    possible_injured_count: int = 0
    detected_hazards: List[HazardDetection] = []
    audio_transcript: Optional[str] = None
    audio_transcript_uncertain: bool = False
    visual_detections: List[Dict[str, Any]] = []
    recommended_priority: str
    priority_reason: str
    confidence: float
    citations: List[str] = []


class IncidentCombinedAIAnalysisResponse(BaseModel):
    incident_id: str
    emergency_type: str
    incident_summary: str
    affected_locations: List[Dict[str, Any]] = []
    report_count: int
    possible_people_affected: int
    possible_people_trapped: int
    identified_hazards: List[HazardDetection] = []
    missing_critical_information: List[str] = []
    recommended_priority: str
    priority_rationale: str
    recommended_next_actions: List[str] = []
    confidence: float
    supporting_evidence: List[Dict[str, Any]] = []
