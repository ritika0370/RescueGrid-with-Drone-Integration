"""
Twilio Inbound Emergency Voice Call Service.
Enables citizens to call directly via phone to report emergencies.
Automatically captures caller audio, transcribes speech, extracts location and category,
creates an SOS Report, groups it into the disaster incident, and feeds it into the live dashboard.
"""
import logging
import re
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.twilio_call import TwilioCallLog
from app.models.report import Report
from app.schemas.report import ReportCreateRequest, EmergencyCategory, ReporterSafetyStatus
from app.services.report_service import ReportService
from app.core.events import event_manager
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class TwilioEmergencyService:
    @staticmethod
    def generate_incoming_twiml(call_sid: str) -> str:
        """
        Generate TwiML XML greeting the caller and prompting for emergency details.
        Uses <Gather input="speech"> with fallback to <Record>.
        """
        base_url = settings.TWILIO_WEBHOOK_BASE_URL.rstrip("/")
        speech_action = f"{base_url}/api/v1/twilio/voice/process-speech"
        record_action = f"{base_url}/api/v1/twilio/voice/recording-callback"
        transcribe_cb = f"{base_url}/api/v1/twilio/voice/transcription-callback"

        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna" language="en-US">
        Disaster Response Emergency Hotline. You are connected to the automated emergency dispatch agent.
        Please describe your emergency, your location or landmark, and if anyone is trapped or injured.
    </Say>
    <Gather input="speech" action="{speech_action}" method="POST" timeout="6" speechTimeout="auto" language="en-US">
        <Say voice="Polly.Joanna">Please speak clearly now.</Say>
    </Gather>
    <Say voice="Polly.Joanna">We did not detect your voice. Please leave your emergency message after the beep.</Say>
    <Record action="{record_action}" method="POST" maxLength="120" playBeep="true" transcribe="true" transcribeCallback="{transcribe_cb}" />
    <Say voice="Polly.Joanna">Thank you. Your call has been recorded and submitted to rescue dispatch.</Say>
    <Hangup/>
</Response>"""
        return twiml

    @staticmethod
    def classify_emergency_category(speech_text: str) -> EmergencyCategory:
        """Classify spoken text into standard emergency categories."""
        text = speech_text.lower()
        if any(w in text for w in ["flood", "water rising", "drowning", "river overflow", "submerged"]):
            return EmergencyCategory.FLOOD
        if any(w in text for w in ["fire", "blaze", "burning", "smoke", "flames"]):
            return EmergencyCategory.FIRE
        if any(w in text for w in ["earthquake", "tremor", "ground shaking", "aftershock"]):
            return EmergencyCategory.EARTHQUAKE
        if any(w in text for w in ["collapse", "building fell", "roof collapsed", "rubble", "wall fell"]):
            return EmergencyCategory.BUILDING_COLLAPSE
        if any(w in text for w in ["accident", "car crash", "collision", "vehicle", "highway"]):
            return EmergencyCategory.ROAD_ACCIDENT
        if any(w in text for w in ["heart attack", "unconscious", "stroke", "bleeding", "ambulance", "breathing"]):
            return EmergencyCategory.MEDICAL_EMERGENCY
        if any(w in text for w in ["chemical", "gas leak", "toxic", "fumes", "explosion", "industrial"]):
            return EmergencyCategory.INDUSTRIAL_OR_CHEMICAL_INCIDENT
        if any(w in text for w in ["missing", "trapped", "lost person", "stuck in elevator"]):
            return EmergencyCategory.MISSING_OR_TRAPPED_PERSON
        return EmergencyCategory.OTHER_EMERGENCY

    @classmethod
    async def log_incoming_call(
        cls,
        db: AsyncSession,
        call_sid: str,
        from_phone: str,
        to_phone: str,
        caller_city: Optional[str] = None,
        caller_state: Optional[str] = None,
        caller_zip: Optional[str] = None,
    ) -> TwilioCallLog:
        """Log incoming phone call record in database (idempotent for repeat call_sid)."""
        res = await db.execute(select(TwilioCallLog).where(TwilioCallLog.call_sid == call_sid))
        call_log = res.scalar_one_or_none()
        if call_log:
            call_log.from_phone = from_phone
            call_log.to_phone = to_phone
            call_log.caller_city = caller_city
            call_log.caller_state = caller_state
            call_log.caller_zip = caller_zip
        else:
            call_log = TwilioCallLog(
                call_sid=call_sid,
                from_phone=from_phone,
                to_phone=to_phone,
                caller_city=caller_city,
                caller_state=caller_state,
                caller_zip=caller_zip,
                status="INCOMING",
                created_at=datetime.now(timezone.utc),
            )
            db.add(call_log)
        await db.commit()
        await db.refresh(call_log)
        return call_log

    @classmethod
    async def process_speech_gather(
        cls,
        db: AsyncSession,
        call_sid: str,
        from_phone: str,
        speech_result: str,
        confidence: Optional[float] = None,
        caller_city: Optional[str] = None,
        caller_state: Optional[str] = None,
    ) -> Tuple[Report, str]:
        """
        Process Twilio gathered speech:
        1. Auto-extract category & location
        2. Feed into Citizen SOS Report system
        3. Trigger AI & Grouping pipeline
        4. Broadcast live notification to dispatch website
        5. Return acknowledgment TwiML
        """
        category = cls.classify_emergency_category(speech_result)
        
        # Determine location from Twilio metadata or speech text
        loc_str = ""
        if caller_city and caller_state:
            loc_str = f"{caller_city}, {caller_state}"
        elif caller_city:
            loc_str = caller_city
        else:
            # Extract from text if mentioned
            loc_match = re.search(r"(?:at|in|near)\s+([A-Za-z0-9\s,\.-]+?)(?=\.|\band\b|$)", speech_result, re.IGNORECASE)
            loc_str = loc_match.group(1).strip() if loc_match else "Phone call location"

        # Check trapped indicators
        people_trapped = 1 if any(w in speech_result.lower() for w in ["trapped", "stranded", "stuck"]) else 0

        # Construct Report request
        report_req = ReportCreateRequest(
            reporter_phone=from_phone,
            reporter_name=f"Caller ({from_phone})",
            emergency_category=category,
            description=f"[TWILIO EMERGENCY CALL]: {speech_result}",
            address_or_landmark=loc_str,
            people_affected=1,
            people_trapped=people_trapped,
            reporter_safety_status=ReporterSafetyStatus.AT_RISK if people_trapped else ReporterSafetyStatus.UNKNOWN,
            submission_source="TWILIO_VOICE",
        )

        ack = await ReportService.ingest_report(db, report_req)
        
        # Link Call Log to Report (create log if incoming webhook was not previously called)
        res = await db.execute(select(TwilioCallLog).where(TwilioCallLog.call_sid == call_sid))
        call_log = res.scalar_one_or_none()
        if not call_log:
            call_log = TwilioCallLog(
                call_sid=call_sid,
                from_phone=from_phone,
                to_phone=settings.TWILIO_PHONE_NUMBER,
                caller_city=caller_city,
                caller_state=caller_state,
                linked_report_id=ack.report_id,
                transcription_text=speech_result,
                status="REPORT_CREATED",
                created_at=datetime.now(timezone.utc),
            )
            db.add(call_log)
        else:
            call_log.linked_report_id = ack.report_id
            call_log.transcription_text = speech_result
            call_log.status = "REPORT_CREATED"
        await db.commit()

        # Trigger async AI & Grouping pipeline
        await ReportService.process_report_pipeline(db, ack.report_id)

        # Audit log
        await AuditService.log_action(
            db,
            action="TWILIO_CALL_INGESTED",
            entity_type="REPORT",
            entity_id=ack.report_id,
            details={
                "call_sid": call_sid,
                "from_phone": from_phone,
                "speech_result": speech_result,
                "category": category.value,
            },
        )

        # Broadcast event to WebSockets for live website update
        await event_manager.broadcast_global(
            "TWILIO_CALL_REPORT_FEED",
            {
                "report_id": ack.report_id,
                "from_phone": from_phone,
                "category": category.value,
                "location": loc_str,
                "transcript": speech_result,
                "trapped": people_trapped,
            },
        )

        response_twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna" language="en-US">
        Your emergency report has been automatically fed into the emergency coordination dashboard.
        Rescue units and dispatchers are reviewing your incident. Stay safe. Help is being coordinated.
    </Say>
    <Hangup/>
</Response>"""
        
        rep_res = await db.execute(select(Report).where(Report.id == ack.report_id))
        report = rep_res.scalar_one()
        return report, response_twiml
