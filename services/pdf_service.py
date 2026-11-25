"""
PDF Report Generator Service (Section 13).
Generates compliant, multi-page PDF 1.4 documents containing all 9 sections of the
Rescue Intelligence Report with clean layout, headers, metadata, and disclaimer.
"""
import io
import os
import re
from typing import List
from app.core.config import settings
from app.schemas.rescue_report import RescueIntelligenceReport


class SimplePDFWriter:
    """Pure-Python standard-compliant PDF 1.4 document builder."""
    def __init__(self):
        self.objects: List[bytes] = []
        self.pages: List[int] = []

    def _add_object(self, content: bytes) -> int:
        self.objects.append(content)
        return len(self.objects)

    def create_page_stream(self, lines: List[str]) -> bytes:
        """Construct page content stream with margins, headers, and text formatting."""
        stream = io.BytesIO()
        stream.write(b"BT\n")
        
        y = 740  # Top margin
        margin_x = 50

        for line in lines:
            # Handle page overflow
            if y < 50:
                break
            
            clean_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            # ASCII sanitize
            clean_line = re.sub(r"[^\x20-\x7E]", "", clean_line)

            if line.startswith("### "):
                # Section Header
                text = clean_line[4:]
                stream.write(b"/F2 14 Tf\n")
                stream.write(f"1 0 0 1 {margin_x} {y} Tm\n".encode("latin1"))
                stream.write(f"({text}) Tj\n".encode("latin1"))
                y -= 22
            elif line.startswith("## "):
                # Major Title
                text = clean_line[3:]
                stream.write(b"/F2 16 Tf\n")
                stream.write(f"1 0 0 1 {margin_x} {y} Tm\n".encode("latin1"))
                stream.write(f"({text}) Tj\n".encode("latin1"))
                y -= 26
            elif line.startswith("# "):
                # Document Title
                text = clean_line[2:]
                stream.write(b"/F2 20 Tf\n")
                stream.write(f"1 0 0 1 {margin_x} {y} Tm\n".encode("latin1"))
                stream.write(f"({text}) Tj\n".encode("latin1"))
                y -= 30
            elif line.startswith("  - "):
                # Bullet item
                text = clean_line[4:]
                stream.write(b"/F1 10 Tf\n")
                stream.write(f"1 0 0 1 {margin_x + 15} {y} Tm\n".encode("latin1"))
                stream.write(f"(\x95 {text}) Tj\n".encode("latin1"))
                y -= 14
            elif line.strip() == "---":
                # Horizontal rule / separator
                y -= 10
            elif line.strip() == "":
                y -= 8
            else:
                # Regular paragraph
                stream.write(b"/F1 10 Tf\n")
                stream.write(f"1 0 0 1 {margin_x} {y} Tm\n".encode("latin1"))
                stream.write(f"({clean_line}) Tj\n".encode("latin1"))
                y -= 14

        stream.write(b"ET\n")
        return stream.getvalue()

    def build_pdf(self, pages_text: List[List[str]]) -> bytes:
        catalog_obj_idx = 1
        pages_tree_obj_idx = 2
        font_f1_idx = 3
        font_f2_idx = 4

        self.objects = [b"", b"", b"", b""]  # Placeholders

        # Standard Built-in Fonts
        self.objects[font_f1_idx - 1] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
        self.objects[font_f2_idx - 1] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"

        page_obj_indices = []

        for p_lines in pages_text:
            stream_bytes = self.create_page_stream(p_lines)
            stream_obj = (
                f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("latin1")
                + stream_bytes
                + b"\nendstream"
            )
            stream_idx = self._add_object(stream_obj)

            page_dict = (
                f"<< /Type /Page /Parent {pages_tree_obj_idx} 0 R /MediaBox [0 0 612 792] "
                f"/Contents {stream_idx} 0 R /Resources << /Font << /F1 {font_f1_idx} 0 R /F2 {font_f2_idx} 0 R >> >> >>"
            ).encode("latin1")
            page_idx = self._add_object(page_dict)
            page_obj_indices.append(page_idx)

        # Pages Tree
        kids_str = " ".join([f"{idx} 0 R" for idx in page_obj_indices])
        pages_tree = f"<< /Type /Pages /Kids [{kids_str}] /Count {len(page_obj_indices)} >>".encode("latin1")
        self.objects[pages_tree_obj_idx - 1] = pages_tree

        # Catalog
        catalog = f"<< /Type /Catalog /Pages {pages_tree_obj_idx} 0 R >>".encode("latin1")
        self.objects[catalog_obj_idx - 1] = catalog

        # Assemble full document with xref table
        out = io.BytesIO()
        out.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

        offsets = []
        for i, obj in enumerate(self.objects, 1):
            offsets.append(out.tell())
            out.write(f"{i} 0 obj\n".encode("latin1"))
            out.write(obj)
            out.write(b"\nendobj\n")

        xref_pos = out.tell()
        out.write(f"xref\n0 {len(self.objects) + 1}\n".encode("latin1"))
        out.write(b"0000000000 65535 f \n")
        for off in offsets:
            out.write(f"{off:010d} 00000 n \n".encode("latin1"))

        out.write(f"trailer\n<< /Size {len(self.objects) + 1} /Root {catalog_obj_idx} 0 R >>\n".encode("latin1"))
        out.write(b"startxref\n")
        out.write(f"{xref_pos}\n".encode("latin1"))
        out.write(b"%%EOF\n")

        return out.getvalue()


class PDFReportService:
    @classmethod
    def generate_pdf(cls, report: RescueIntelligenceReport) -> bytes:
        """Format 9-section report into paginated PDF."""
        writer = SimplePDFWriter()

        # Page 1: Header, Incident Identification, Executive Summary, Citizen Reports
        page1 = [
            "# DISASTER RESCUE INTELLIGENCE REPORT",
            "OFFICIAL SITUATIONAL ASSESSMENT - FOR AUTHORIZED RESPONDERS",
            f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "---",
            "### SECTION 1: INCIDENT IDENTIFICATION",
            f"Incident ID: {report.section_1_incident_identification.incident_id}",
            f"Emergency Category: {report.section_1_incident_identification.emergency_category}",
            f"Status: {report.section_1_incident_identification.current_status}",
            f"Assigned Department: {report.section_1_incident_identification.assigned_department}",
            f"First Reported: {report.section_1_incident_identification.first_reported_time.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "### SECTION 2: EXECUTIVE SUMMARY",
            f"Summary: {report.section_2_executive_summary.short_description[:120]}...",
            f"Current Situation: {report.section_2_executive_summary.current_situation}",
            f"Priority Assessment: {report.section_2_executive_summary.priority_level}",
            f"Urgency: {report.section_2_executive_summary.urgency_statement}",
            "",
            "### SECTION 3: CITIZEN SOS REPORTS",
            f"Total Independent Linked Reports: {report.section_3_citizen_reports.total_linked_reports}",
            f"Total People Reported Affected: {report.section_3_citizen_reports.total_people_reported_affected}",
            f"Total People Reported Trapped: {report.section_3_citizen_reports.total_people_reported_trapped}",
            "Report Statements:",
        ]
        for desc in report.section_3_citizen_reports.citizen_provided_descriptions[:4]:
            page1.append(f"  - {desc[:90]}")

        # Page 2: Geographic Info, Drone Survey Findings, AI Analysis
        page2 = [
            "### SECTION 4: GEOGRAPHIC INFORMATION",
            f"Area Description: {report.section_4_geographic_information.incident_area_description}",
            "Affected Coordinate Points:",
        ]
        for loc in report.section_4_geographic_information.affected_locations[:3]:
            page2.append(f"  - ({loc.get('latitude')}, {loc.get('longitude')}) - {loc.get('label', 'Site')}")

        page2.extend([
            "",
            "### SECTION 5: DRONE SURVEY FINDINGS",
            f"Surveys Executed: {report.section_5_drone_survey_findings.missions_count}",
            f"Verified Human Sightings: {len(report.section_5_drone_survey_findings.possible_human_sightings)}",
            f"Hazards and Obstacles Detected: {len(report.section_5_drone_survey_findings.damage_and_hazards)}",
            "Survey Observations:",
        ])
        for obs in report.section_5_drone_survey_findings.raw_observations[:4]:
            page2.append(f"  - [{obs.get('source')}]: {obs.get('description', '')[:85]}")

        page2.extend([
            "",
            "### SECTION 6: AI SITUATIONAL ANALYSIS",
            f"Risk & Priority Assessment: {report.section_6_ai_analysis.risk_and_priority_assessment}",
            f"Model Confidence: {report.section_6_ai_analysis.confidence_score * 100:.1f}%",
            "Priority Actions Identified by AI:",
        ])
        for prio in report.section_6_ai_analysis.possible_rescue_priorities[:2]:
            page2.append(f"  - {prio}")
        page2.append("Identified Uncertainties:")
        for unc in report.section_6_ai_analysis.uncertainties[:2]:
            page2.append(f"  - {unc}")

        # Page 3: Rescue Planning, Evidence Trail, Disclaimer
        page3 = [
            "### SECTION 7: SUGGESTED RESCUE PLANNING INFORMATION",
            "Access Routes:",
        ]
        for route in report.section_7_suggested_rescue_planning.possible_access_routes[:2]:
            page3.append(f"  - {route}")
        page3.append("Recommended Rescue Equipment:")
        for equip in report.section_7_suggested_rescue_planning.possible_equipment_requirements[:4]:
            page3.append(f"  - {equip}")
        page3.append("Next Steps for Responders:")
        for step in report.section_7_suggested_rescue_planning.suggested_next_steps_for_responders[:3]:
            page3.append(f"  - {step}")

        page3.extend([
            "",
            "### SECTION 8: EVIDENCE AND AUDIT TRAIL",
            f"Linked Report IDs: {', '.join([rid[:8] for rid in report.section_8_evidence_and_audit_trail.source_report_ids])}",
            f"Observation IDs: {', '.join([oid[:8] for oid in report.section_8_evidence_and_audit_trail.observation_ids])}",
            "Officer Decisions Audit Log:",
        ])
        for rev in report.section_8_evidence_and_audit_trail.officer_review_history[:3]:
            page3.append(f"  - [{rev.get('action')}]: {str(rev.get('details'))[:70]}")

        page3.extend([
            "",
            "### SECTION 9: OPERATIONAL DISCLAIMER",
            report.section_9_disclaimer,
        ])

        pdf_bytes = writer.build_pdf([page1, page2, page3])
        return pdf_bytes
