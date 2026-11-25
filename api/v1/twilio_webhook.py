"""
Twilio Inbound Voice Call Webhook API.
Handles live phone calls from citizens reporting disasters:
1. Gathers speech or records audio via TwiML.
2. Automatically extracts emergency details and feeds them into the live website.
3. Triggers AI classification, grouping, and dispatcher alerting.
"""
from typing import List
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_officer
from app.models.twilio_call import TwilioCallLog
from app.schemas.twilio import TwilioCallRecordResponse
from app.services.twilio_service import TwilioEmergencyService

router = APIRouter(prefix="/twilio/voice", tags=["Twilio Emergency Voice Hotline"])


@router.post("/incoming")
async def incoming_call_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Twilio Inbound Voice Webhook.
    Invoked when a citizen dials the emergency phone hotline.
    Returns TwiML prompting the caller to state their emergency and location.
    """
    form_data = await request.form()
    call_sid = str(form_data.get("CallSid", "SIMULATED_CALL_SID"))
    from_phone = str(form_data.get("From", "+15550001234"))
    to_phone = str(form_data.get("To", "+18005550199"))
    caller_city = form_data.get("CallerCity")
    caller_state = form_data.get("CallerState")
    caller_zip = form_data.get("CallerZip")

    # Log incoming call in database
    await TwilioEmergencyService.log_incoming_call(
        db=db,
        call_sid=call_sid,
        from_phone=from_phone,
        to_phone=to_phone,
        caller_city=caller_city,
        caller_state=caller_state,
        caller_zip=caller_zip,
    )

    twiml_xml = TwilioEmergencyService.generate_incoming_twiml(call_sid)
    return Response(content=twiml_xml, media_type="application/xml")


@router.post("/process-speech")
async def process_speech_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Twilio Gather Speech Callback Webhook.
    Receives transcribed speech from caller, automatically creates an emergency report,
    groups it into an incident, alerts officers, and informs the caller.
    """
    form_data = await request.form()
    call_sid = str(form_data.get("CallSid", "SIMULATED_CALL_SID"))
    from_phone = str(form_data.get("From", "+15550001234"))
    speech_result = str(form_data.get("SpeechResult", "Emergency reported via phone call."))
    confidence_str = form_data.get("Confidence")
    confidence = float(confidence_str) if confidence_str else 0.90
    caller_city = form_data.get("CallerCity")
    caller_state = form_data.get("CallerState")

    report, twiml_response = await TwilioEmergencyService.process_speech_gather(
        db=db,
        call_sid=call_sid,
        from_phone=from_phone,
        speech_result=speech_result,
        confidence=confidence,
        caller_city=caller_city,
        caller_state=caller_state,
    )

    return Response(content=twiml_response, media_type="application/xml")


@router.post("/recording-callback")
async def recording_callback_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Twilio Recording Status Callback Webhook.
    Receives the URL of the recorded voicemail audio when a caller leaves a message.
    """
    form_data = await request.form()
    call_sid = str(form_data.get("CallSid", ""))
    recording_url = str(form_data.get("RecordingUrl", ""))
    duration = form_data.get("RecordingDuration")

    res = await db.execute(select(TwilioCallLog).where(TwilioCallLog.call_sid == call_sid))
    call_log = res.scalar_one_or_none()
    if call_log:
        call_log.recording_url = recording_url
        if duration:
            try:
                call_log.recording_duration = int(duration)
            except ValueError:
                pass
        call_log.status = "RECORDED"
        await db.commit()

    return Response(
        content="<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response><Hangup/></Response>",
        media_type="application/xml",
    )


@router.post("/transcription-callback")
async def transcription_callback_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Twilio Voice Transcription Callback Webhook.
    Receives automated transcript of recorded voicemails.
    """
    form_data = await request.form()
    call_sid = str(form_data.get("CallSid", ""))
    transcription_text = str(form_data.get("TranscriptionText", ""))

    res = await db.execute(select(TwilioCallLog).where(TwilioCallLog.call_sid == call_sid))
    call_log = res.scalar_one_or_none()
    if call_log:
        call_log.transcription_text = transcription_text
        call_log.status = "TRANSCRIBED"
        await db.commit()

    return {"status": "transcription_received"}


@router.get("/calls", response_model=List[TwilioCallRecordResponse])
async def list_emergency_calls(
    db: AsyncSession = Depends(get_db),
    officer=Depends(require_officer),
):
    """List all emergency phone calls received by the Twilio hotline."""
    res = await db.execute(select(TwilioCallLog).order_by(TwilioCallLog.created_at.desc()))
    return res.scalars().all()
