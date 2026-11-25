"""
Priority Assessment Engine (Section 7).
Transparent, explainable recommendation engine prioritizing life-saving actions.
Supports officer overrides while strictly auditing the override rationale.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


class PriorityAssessmentService:
    @staticmethod
    def assess_priority(
        category: str,
        description: str,
        people_affected: int = 0,
        people_trapped: int = 0,
        safety_status: str = "UNKNOWN",
        hazards: Optional[List[str]] = None,
        first_reported_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate emergency severity and return transparent recommendation:
        P1 - Critical, P2 - High, P3 - Medium, P4 - Low.
        """
        hazards = hazards or []
        desc_lower = description.lower()
        
        score = 0
        reasons = []
        missing_info = []

        has_negated_trapped = any(neg in desc_lower for neg in ["no trapped", "not trapped", "zero trapped", "none trapped", "nobody trapped", "no one trapped"])
        has_trapped_term = ("trapped" in desc_lower or "stranded" in desc_lower) and not has_negated_trapped

        # 1. Trapped and Life Threat Assessment (NIST / FEMA criteria)
        if people_trapped > 0 or safety_status == "TRAPPED" or has_trapped_term:
            score += 50
            reasons.append(f"Immediate life threat: {max(people_trapped, 1)} person(s) reported trapped or stranded.")

        # 2. Category & Physical Severity
        if category in ["Building collapse", "Industrial or chemical incident"]:
            score += 35
            reasons.append(f"Severe infrastructure risk from category: {category}.")
        elif category in ["Fire", "Flood", "Earthquake"]:
            score += 25
            reasons.append(f"High risk natural/hazard event: {category}.")
        elif category in ["Road accident", "Medical emergency"]:
            score += 20
            reasons.append(f"Critical human impact event: {category}.")

        # 3. People Affected Scale
        if people_affected >= 10:
            score += 25
            reasons.append(f"Substantial population affected ({people_affected}+ people reported).")
        elif people_affected >= 3:
            score += 15
            reasons.append(f"Multiple individuals affected ({people_affected} people reported).")

        # 4. Critical Keywords and Visual Hazards
        critical_keywords = ["unconscious", "drowning", "suffocating", "severe bleeding", "collapse", "rising fast", "explosion", "toxic"]
        matched_critical = [w for w in critical_keywords if w in desc_lower]
        if matched_critical:
            score += 20
            reasons.append(f"High urgency indicators detected: {', '.join(matched_critical)}.")

        # 5. Elapsed Time Urgency
        if first_reported_at:
            now = datetime.now(timezone.utc)
            delta_min = (now - first_reported_at.replace(tzinfo=timezone.utc if first_reported_at.tzinfo is None else first_reported_at.tzinfo)).total_seconds() / 60.0
            if delta_min > 60 and score >= 30:
                score += 10
                reasons.append(f"Time-sensitive: Emergency uncontained for >{int(delta_min)} minutes.")

        # Evaluate Missing Information
        if people_affected == 0:
            missing_info.append("Precise count of affected persons is unconfirmed.")
        if people_trapped == 0 and "trapped" not in desc_lower:
            missing_info.append("Trapped victim count not definitively stated.")
        if not hazards:
            missing_info.append("Ground visual hazard confirmation pending.")

        # Priority Level Assignment
        if score >= 60:
            priority = "P1"
            urgency = "Critical - Immediate Life Safety Threat"
            confidence = 0.90
        elif score >= 40:
            priority = "P2"
            urgency = "High - Significant Threat to Life or Property"
            confidence = 0.85
        elif score >= 20:
            priority = "P3"
            urgency = "Medium - Urgent Response Required"
            confidence = 0.80
        else:
            priority = "P4"
            urgency = "Low - Routine Emergency or Monitoring"
            confidence = 0.75

        # Safety rule: Never downgrade confirmed trapped or life threatening
        if (people_trapped > 0 or safety_status == "TRAPPED") and priority not in ["P1", "P2"]:
            priority = "P1"
            reasons.append("Safety Guardrail: Confirmed trapped victims escalated priority to P1.")

        return {
            "recommended_priority": priority,
            "urgency_statement": urgency,
            "score": score,
            "reasons": reasons,
            "missing_information": missing_info,
            "confidence": confidence,
            "disclaimer": "Priority is an advisory recommendation. Qualified emergency officers retain final override authority.",
        }
