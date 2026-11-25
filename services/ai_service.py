"""
AI Emergency Analysis Engine (Section 6).
Processes multimodal inputs (Text, Audio, Vision) and provides combined incident intelligence.
Distinguishes confirmed citizen statements from AI detections and maintains clear citation links.
"""
import re
from typing import Any, Dict, List, Optional
from app.adapters import get_stt_adapter, get_vision_adapter
from app.models.ai_analysis import AIAnalysis
from app.models.report import Report
from app.models.incident import Incident
from app.services.priority_service import PriorityAssessmentService
from sqlalchemy.ext.asyncio import AsyncSession


class AIEmergencyAnalysisEngine:
    @classmethod
    def analyze_text(cls, text: str, category: str) -> Dict[str, Any]:
        """Extract structured emergency intelligence from text descriptions."""
        text_lower = text.lower()
        extracted_locations = []
        hazards = []
        possible_trapped = 0
        possible_injured = 0
        urgency_indicators = []

        # Location heuristic extraction
        loc_patterns = [
            r"at\s+([A-Za-z0-9\s,\.-]+?)(?=\.|\band\b|\bwith\b|\bwhere\b|$)",
            r"near\s+([A-Za-z0-9\s,\.-]+?)(?=\.|\band\b|\bwith\b|\bwhere\b|$)",
            r"on\s+([A-Za-z0-9\s,\.-]+?)(?=\.|\band\b|\bwith\b|\bwhere\b|$)",
            r"street\s+([A-Za-z0-9\s]+)",
            r"block\s+([A-Za-z0-9\s]+)",
        ]
        for pat in loc_patterns:
            matches = re.findall(pat, text, re.IGNORECASE)
            for m in matches:
                loc = m.strip()
                if len(loc) > 3 and loc not in extracted_locations:
                    extracted_locations.append(loc)

        # Hazard detection in text
        if any(w in text_lower for w in ["flood", "water", "inundat", "submerged", "overflow"]):
            hazards.append({
                "hazard_type": "FLOODWATER",
                "severity": "HIGH",
                "description": "Rising floodwater reported entering structures/streets",
                "confidence": 0.92,
                "source": "CITIZEN_STATEMENT",
            })
        if any(w in text_lower for w in ["fire", "blaze", "burning", "flame"]):
            hazards.append({
                "hazard_type": "FIRE",
                "severity": "CRITICAL",
                "description": "Active fire or open combustion reported",
                "confidence": 0.95,
                "source": "CITIZEN_STATEMENT",
            })
        if any(w in text_lower for w in ["smoke", "suffocat", "fumes"]):
            hazards.append({
                "hazard_type": "SMOKE_INHALATION",
                "severity": "HIGH",
                "description": "Smoke accumulation reported",
                "confidence": 0.88,
                "source": "CITIZEN_STATEMENT",
            })
        if any(w in text_lower for w in ["wire", "electric", "pole", "current", "shock"]):
            hazards.append({
                "hazard_type": "ELECTRICAL_HAZARD",
                "severity": "CRITICAL",
                "description": "Live electrical hazard or damaged wires reported",
                "confidence": 0.85,
                "source": "CITIZEN_STATEMENT",
            })
        if any(w in text_lower for w in ["collapse", "cracked wall", "rubble", "debris"]):
            hazards.append({
                "hazard_type": "STRUCTURAL_COLLAPSE",
                "severity": "CRITICAL",
                "description": "Building structural failure or debris collapse",
                "confidence": 0.90,
                "source": "CITIZEN_STATEMENT",
            })

        # Trapped people detection
        trapped_match = re.search(r"(\d+)\s*(?:people|persons|residents|victims)?\s*(?:are\s*)?(?:trapped|stranded|stuck)", text_lower)
        if trapped_match:
            try:
                possible_trapped = int(trapped_match.group(1))
            except ValueError:
                possible_trapped = 1
        elif "trapped" in text_lower or "stranded" in text_lower:
            possible_trapped = 1

        # Injured people detection
        injured_match = re.search(r"(\d+)\s*(?:people|persons)?\s*(?:are\s*)?(?:injured|hurt|bleeding)", text_lower)
        if injured_match:
            try:
                possible_injured = int(injured_match.group(1))
            except ValueError:
                possible_injured = 1
        elif any(w in text_lower for w in ["injured", "unconscious", "broken leg", "burns"]):
            possible_injured = 1

        # Urgency indicators
        for kw in ["emergency", "urgent", "help", "immediately", "dying", "fast", "asap", "critical"]:
            if kw in text_lower:
                urgency_indicators.append(kw)

        urgency_level = "CRITICAL" if possible_trapped > 0 or "immediately" in text_lower else "HIGH"

        return {
            "emergency_type": category,
            "extracted_locations": extracted_locations,
            "possible_trapped_count": possible_trapped,
            "possible_injured_count": possible_injured,
            "urgency_level": urgency_level,
            "urgency_indicators": urgency_indicators,
            "hazards": hazards,
            "citations": [f"Text statement: '{text[:80]}...'"],
        }

    @classmethod
    def analyze_audio(cls, audio_path: str) -> Dict[str, Any]:
        """Transcribe and extract intelligence from audio."""
        stt = get_stt_adapter()
        stt_result = stt.transcribe(audio_path)
        transcript = stt_result.get("transcript", "")
        text_intel = cls.analyze_text(transcript, category="Audio Emergency Report")
        return {
            "transcript": transcript,
            "confidence": stt_result.get("confidence", 0.8),
            "language": stt_result.get("language", "en"),
            "is_uncertain": stt_result.get("is_uncertain", False),
            "intelligence": text_intel,
        }

    @classmethod
    def analyze_image(cls, image_path: str) -> Dict[str, Any]:
        """Analyze image with configured computer vision adapter."""
        vision = get_vision_adapter()
        return vision.analyze_image(image_path)

    @classmethod
    def combine_incident_reports(cls, incident: Incident, reports: List[Report]) -> Dict[str, Any]:
        """
        Synthesize multi-source reports for an incident into a unified situational analysis.
        Strictly preserves citations and avoids hallucinating missing data.
        """
        all_hazards = []
        all_locations = []
        total_trapped = 0
        total_affected = 0
        descriptions = []
        citations = []

        for r in reports:
            total_trapped += r.people_trapped
            total_affected += r.people_affected
            descriptions.append(r.description)
            citations.append(f"Report {r.id[:8]}: ({r.latitude}, {r.longitude}) - '{r.description[:50]}...'")

            if r.latitude and r.longitude:
                all_locations.append({
                    "report_id": r.id,
                    "latitude": r.latitude,
                    "longitude": r.longitude,
                    "landmark": r.address_or_landmark or r.manually_entered_location or "Report coordinate",
                })

            text_analysis = cls.analyze_text(r.description, r.emergency_category)
            for h in text_analysis["hazards"]:
                if not any(existing["hazard_type"] == h["hazard_type"] for existing in all_hazards):
                    all_hazards.append(h)

        combined_desc = " ".join(descriptions)
        text_synthesis = cls.analyze_text(combined_desc, incident.emergency_category)

        # Priority calculation
        priority_eval = PriorityAssessmentService.assess_priority(
            category=incident.emergency_category,
            description=combined_desc,
            people_affected=total_affected,
            people_trapped=total_trapped,
            hazards=[h["hazard_type"] for h in all_hazards],
            first_reported_at=incident.first_reported_at,
        )

        missing_critical_info = []
        if not all_locations:
            missing_critical_info.append("Precise geocoordinates for ground response.")
        if total_trapped == 0:
            missing_critical_info.append("Ground search needed to verify whether trapped persons remain unlocated.")
        missing_critical_info.append("Structural integrity assessment from qualified engineer or drone survey.")

        recommended_next_actions = [
            "Deploy aerial drone reconnaissance to verify extent of flooded/damaged sectors.",
            "Establish perimeter and staging area outside identified hazard zone.",
            "Dispatch prioritized ground rescue units to verified trapped locations.",
            "Coordinate with medical emergency units for potential triage.",
        ]

        summary = (
            f"Active {incident.emergency_category} emergency impacting {len(reports)} reporting citizen(s). "
            f"Estimated {total_affected} people affected with {total_trapped} reported trapped or stranded. "
            f"Key hazards identified: {', '.join([h['hazard_type'] for h in all_hazards]) or 'General emergency hazards'}."
        )

        return {
            "incident_id": incident.id,
            "emergency_type": incident.emergency_category,
            "incident_summary": summary,
            "affected_locations": all_locations,
            "report_count": len(reports),
            "possible_people_affected": total_affected,
            "possible_people_trapped": total_trapped,
            "identified_hazards": all_hazards,
            "missing_critical_information": missing_critical_info,
            "recommended_priority": priority_eval["recommended_priority"],
            "priority_rationale": "; ".join(priority_eval["reasons"]),
            "recommended_next_actions": recommended_next_actions,
            "confidence": 0.88,
            "supporting_evidence": [{"report_citations": citations}],
        }
