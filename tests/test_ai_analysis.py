"""
Tests for AI Multimodal Emergency Analysis Engine (Section 6 & 7).
"""
import pytest
from app.services.ai_service import AIEmergencyAnalysisEngine
from app.services.priority_service import PriorityAssessmentService


def test_nlp_emergency_text_extraction():
    text = "Emergency! 3 people are trapped in the attic near Elm Street. Flood water is rising rapidly past the windows!"
    intel = AIEmergencyAnalysisEngine.analyze_text(text, category="Flood")
    assert intel["possible_trapped_count"] == 3
    assert intel["urgency_level"] == "CRITICAL"
    assert any(h["hazard_type"] == "FLOODWATER" for h in intel["hazards"])
    assert len(intel["extracted_locations"]) >= 1


def test_priority_assessment_p1_for_trapped_persons():
    res = PriorityAssessmentService.assess_priority(
        category="Building collapse",
        description="Building partially collapsed. 5 people trapped under concrete debris.",
        people_affected=8,
        people_trapped=5,
        safety_status="TRAPPED",
    )
    assert res["recommended_priority"] == "P1"
    assert res["score"] >= 60
    assert any("trapped" in r.lower() for r in res["reasons"])


def test_priority_assessment_p3_for_minor_incident():
    res = PriorityAssessmentService.assess_priority(
        category="Road accident",
        description="Fender bender on side street. No trapped victims, traffic moving slowly.",
        people_affected=1,
        people_trapped=0,
        safety_status="SAFE",
    )
    assert res["recommended_priority"] in ["P3", "P4"]
