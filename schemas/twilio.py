"""
Twilio Inbound Voice Call and TwiML Schemas.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TwilioVoiceWebhookRequest(BaseModel):
    CallSid: str
    From: str
    To: str
    CallerCity: Optional[str] = None
    CallerState: Optional[str] = None
    CallerZip: Optional[str] = None
    CallerCountry: Optional[str] = None


class TwilioSpeechGatherRequest(BaseModel):
    CallSid: str
    From: str
    To: Optional[str] = None
    SpeechResult: Optional[str] = None
    Confidence: Optional[float] = None
    CallerCity: Optional[str] = None
    CallerState: Optional[str] = None
    CallerZip: Optional[str] = None


class TwilioRecordingCallbackRequest(BaseModel):
    CallSid: str
    RecordingSid: str
    RecordingUrl: str
    RecordingDuration: Optional[str] = None


class TwilioTranscriptionCallbackRequest(BaseModel):
    CallSid: Optional[str] = None
    RecordingSid: Optional[str] = None
    TranscriptionText: Optional[str] = None
    TranscriptionStatus: Optional[str] = None


class TwilioCallRecordResponse(BaseModel):
    id: str
    call_sid: str
    from_phone: str
    caller_city: Optional[str] = None
    caller_state: Optional[str] = None
    transcription_text: Optional[str] = None
    recording_url: Optional[str] = None
    linked_report_id: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
