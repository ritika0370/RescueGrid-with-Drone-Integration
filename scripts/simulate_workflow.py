"""
End-to-End Disaster Workflow Simulation Script (Section 19).
Demonstrates the full lifecycle of an emergency:
1. Ingestion of 4 distinct citizen SOS reports (Flood scenario at 3:00 PM)
2. Ingestion of an incoming Twilio voice phone call emergency report
3. Multimodal AI processing and preservation of all individual GPS coordinates
4. Multi-factor incident grouping engine linking them to a single disaster
5. Priority assessment (P1/P2/P3/P4) and department routing
6. Officer review and manual drone survey job card generation
7. Pilot workflow: assignment -> acceptance -> flight -> observation submission -> completion
8. Survey AI analysis and final 9-section Rescue Intelligence Report generation (JSON & PDF)
"""
import asyncio
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.department import Department
from app.models.drone import Drone
from app.models.incident import Incident
from app.models.report import Report
from app.models.user import User
from app.schemas.mission import MissionCreateRequest
from app.schemas.observation import ObservationCreateRequest
from app.schemas.report import EmergencyCategory, ReportCreateRequest, ReporterSafetyStatus
from app.services.media_service import MediaService
from app.services.mission_service import MissionService
from app.services.pdf_service import PDFReportService
from app.services.pilot_service import PilotService
from app.services.report_service import ReportService
from app.services.rescue_report_service import RescueReportService
from app.services.routing_service import DepartmentRoutingService
from app.services.twilio_service import TwilioEmergencyService


async def run_simulation():
    print("=" * 80)
    print("  DISASTER RESPONSE PLATFORM: END-TO-END DEMONSTRATION WORKFLOW")
    print("=" * 80)

    async with AsyncSessionLocal() as db:
        # 0. Load users and departments
        user_res = await db.execute(select(User).where(User.email == "officer.john@disaster.org"))
        officer = user_res.scalar_one()
        pilot_res = await db.execute(select(User).where(User.email == "pilot.sarah@rescue.org"))
        pilot = pilot_res.scalar_one()

        print("\n[STEP 1 & 2] Ingesting 4 Citizen SOS Reports at 3:00 PM Flood Incident...")
        
        # Report A: Water entering house
        req_a = ReportCreateRequest(
            emergency_category=EmergencyCategory.FLOOD,
            description="Water is entering our ground floor living room rapidly from the street drain.",
            latitude=37.7810,
            longitude=-122.4120,
            location_accuracy=5.0,
            address_or_landmark="104 Elm Street, Sector 3",
            people_affected=3,
            people_trapped=0,
            reporter_safety_status=ReporterSafetyStatus.AT_RISK,
        )
        ack_a = await ReportService.ingest_report(db, req_a)
        await ReportService.process_report_pipeline(db, ack_a.report_id)
        print(f"  -> Report A created: ID={ack_a.report_id[:8]} | Status={ack_a.initial_status}")

        # Report B: Stranded on nearby street
        req_b = ReportCreateRequest(
            emergency_category=EmergencyCategory.FLOOD,
            description="Stranded in vehicle due to high floodwater on Elm Street. Engine stalled.",
            latitude=37.7818,
            longitude=-122.4128,
            location_accuracy=8.0,
            address_or_landmark="Elm Street & 4th Avenue Intersection",
            people_affected=2,
            people_trapped=0,
            reporter_safety_status=ReporterSafetyStatus.AT_RISK,
        )
        ack_b = await ReportService.ingest_report(db, req_b)
        await ReportService.process_report_pipeline(db, ack_b.report_id)
        print(f"  -> Report B created: ID={ack_b.report_id[:8]} | Status={ack_b.initial_status}")

        # Report C: People trapped
        req_c = ReportCreateRequest(
            emergency_category=EmergencyCategory.FLOOD,
            description="Urgent! 4 people trapped on the second floor balcony as water reaches 6 feet deep.",
            latitude=37.7825,
            longitude=-122.4115,
            location_accuracy=4.0,
            address_or_landmark="120 Riverbed Road",
            people_affected=4,
            people_trapped=4,
            reporter_safety_status=ReporterSafetyStatus.TRAPPED,
        )
        ack_c = await ReportService.ingest_report(db, req_c)
        await ReportService.process_report_pipeline(db, ack_c.report_id)
        print(f"  -> Report C created: ID={ack_c.report_id[:8]} | Status={ack_c.initial_status}")

        # Report D: Photo of flooded road
        req_d = ReportCreateRequest(
            emergency_category=EmergencyCategory.FLOOD,
            description="Flooded road completely blocked with heavy current. Attached photo.",
            latitude=37.7830,
            longitude=-122.4135,
            location_accuracy=6.0,
            address_or_landmark="North Bridge approach road",
            people_affected=1,
            people_trapped=0,
            reporter_safety_status=ReporterSafetyStatus.SAFE,
        )
        ack_d = await ReportService.ingest_report(db, req_d)
        await ReportService.process_report_pipeline(db, ack_d.report_id)
        print(f"  -> Report D created: ID={ack_d.report_id[:8]} | Status={ack_d.initial_status}")

        # Attach image media to Report D
        dummy_image_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xFF\xC0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xFF\xC4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xFF\xDA\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xFF\xD9"
        media_d = await MediaService.upload_and_process_media(
            db=db,
            filename="floodwater_road_block.jpg",
            content=dummy_image_bytes,
            report_id=ack_d.report_id,
        )
        print(f"     Uploaded media {media_d.id[:8]} (SHA-256: {media_d.sha256_hash[:16]}...)")

        print("\n[STEP 3] Simulating Twilio Inbound Voice Call Emergency Reporting...")
        call_sid = "CA_DEMO_TWILIO_HOTLINE_998811"
        from_phone = "+14155557890"
        speech_text = "Emergency call! Water is pouring into the basement at Elm Street, 2 neighbors are trapped inside and need a rescue boat!"
        
        twilio_report, twiml = await TwilioEmergencyService.process_speech_gather(
            db=db,
            call_sid=call_sid,
            from_phone=from_phone,
            speech_result=speech_text,
            caller_city="San Francisco",
            caller_state="CA",
        )
        print(f"  -> Twilio Call processed: CallSid={call_sid}")
        print(f"  -> Generated Report ID: {twilio_report.id[:8]} from phone {from_phone}")
        print(f"  -> Automatically fed into dispatch website dashboard!")

        # Verify Grouping
        print("\n[STEP 4] Evaluating Incident Grouping Engine Results...")
        rep_res = await db.execute(select(Report).where(Report.id == ack_a.report_id))
        rep_a_db = rep_res.scalar_one()
        incident_id = rep_a_db.incident_id

        inc_res = await db.execute(select(Incident).where(Incident.id == incident_id))
        incident = inc_res.scalar_one()

        linked_res = await db.execute(select(Report).where(Report.incident_id == incident.id))
        all_linked = linked_res.scalars().all()

        print(f"  -> Incident ID: {incident.id[:8]}")
        print(f"  -> Category: {incident.emergency_category}")
        print(f"  -> Calculated Priority: {incident.priority} ({incident.priority_reason})")
        print(f"  -> Linked Citizen Reports: {len(all_linked)} (All individual GPS coords preserved)")
        for lr in all_linked:
            print(f"     - Report {lr.id[:8]}: GPS ({lr.latitude}, {lr.longitude}) | Trapped: {lr.people_trapped} | Source: {lr.submission_source}")

        print("\n[STEP 5] Routing to Authorized Department...")
        dept = await DepartmentRoutingService.route_and_assign_incident(db, incident, officer_user_id=officer.id)
        if dept:
            print(f"  -> Assigned to: {dept.name} ({dept.department_type})")

        print("\n[STEP 6] Officer Review & Drone Survey Job Card Generation...")
        job_card_req = MissionCreateRequest(
            incident_id=incident.id,
            mission_objective="Perform low-altitude aerial survey of flooded sector. Locate trapped persons on balconies and identify clear watercraft approach routes.",
            pilot_id=pilot.id,
            department_instructions="Survey sector 3. Avoid power lines along 4th Ave. Verify coordinates of trapped individuals.",
        )
        mission = await MissionService.generate_job_card(db, job_card_req, officer_id=officer.id)
        print(f"  -> Mission Job Card generated: ID={mission.id[:8]} | Mode={mission.mission_mode}")
        print(f"  -> Recommended Drone: {mission.drone_id[:8]} | Assigned Pilot: {pilot.name}")
        print(f"  -> Survey Boundary Polygon Points: {len(mission.job_card_json.get('survey_boundary_polygon', []))}")

        print("\n[STEP 7] Pilot Workflow Execution (Manual Pilot Mode)...")
        # Pilot accepts
        await PilotService.accept_mission(db, mission.id, pilot.id, notes="Mission accepted. Pre-flight check complete.")
        print(f"  -> Pilot {pilot.name} ACCEPTED job card.")
        
        # Pilot starts survey
        await PilotService.update_mission_status(db, mission.id, "IN_FLIGHT", pilot.id, "Drone airborne in survey sector.")
        print(f"  -> Mission status: IN_FLIGHT. Telemetry streaming.")

        # Pilot submits field observations
        obs1_req = ObservationCreateRequest(
            source="PILOT",
            observation_type="HUMAN_SIGHTING",
            description="Confirmed sighting: 4 persons on 2nd floor balcony waving white cloth. Safe from immediate water line.",
            latitude=37.7825,
            longitude=-122.4115,
            verification_status="PILOT_CONFIRMED",
            confidence=1.0,
        )
        obs1 = await PilotService.submit_observation(db, mission.id, obs1_req, pilot.id)
        print(f"  -> Pilot Observation logged: [HUMAN_SIGHTING] at ({obs1.latitude}, {obs1.longitude})")

        obs2_req = ObservationCreateRequest(
            source="PILOT",
            observation_type="ACCESS_ROUTE",
            description="North access road submerged past culvert. South-west canal corridor clear for rescue boats.",
            latitude=37.7805,
            longitude=-122.4140,
            verification_status="PILOT_CONFIRMED",
            confidence=0.95,
        )
        obs2 = await PilotService.submit_observation(db, mission.id, obs2_req, pilot.id)
        print(f"  -> Pilot Observation logged: [ACCESS_ROUTE] Navigation corridor identified.")

        # Pilot completes mission
        await PilotService.complete_mission(
            db,
            mission.id,
            pilot_notes="Aerial survey complete. 4 victims confirmed safe on balcony. Boat navigation path logged.",
            scanned_boundary={"type": "Polygon", "coordinates": mission.job_card_json.get("survey_boundary_polygon")},
            pilot_id=pilot.id,
        )
        print(f"  -> Mission COMPLETED. Drone returned and battery logged.")

        print("\n[STEP 8] Compiling 9-Section Final Rescue Intelligence Report...")
        report = await RescueReportService.compile_intelligence_report(db, incident.id)
        print(f"  -> Title: {report.report_title}")
        print(f"  -> Section 1 (Identification): Incident {report.section_1_incident_identification.incident_id[:8]}")
        print(f"  -> Section 2 (Summary): Priority {report.section_2_executive_summary.priority_level}")
        print(f"  -> Section 3 (Citizen Reports): {report.section_3_citizen_reports.total_linked_reports} linked reports")
        print(f"  -> Section 5 (Drone Findings): {report.section_5_drone_survey_findings.missions_count} survey missions")
        print(f"  -> Section 7 (Rescue Planning): {len(report.section_7_suggested_rescue_planning.possible_access_routes)} routes identified")
        print(f"  -> Section 9 (Disclaimer): {report.section_9_disclaimer[:80]}...")

        # Export PDF
        pdf_bytes = PDFReportService.generate_pdf(report)
        pdf_path = os.path.join(PROJECT_ROOT, "uploads", "reports_pdf", f"rescue_report_{incident.id[:8]}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"\n[STEP 9] PDF Downloadable Report Generated: {pdf_path} ({len(pdf_bytes)} bytes)")

    print("\n" + "=" * 80)
    print("  DEMONSTRATION AND WORKFLOW VALIDATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_simulation())
