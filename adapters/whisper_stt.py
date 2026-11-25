"""
OpenAI Whisper STT Provider Adapter.
Falls back to MockSTTAdapter if OpenAI API key or whisper library is not configured.
"""
import logging
from typing import Any, Dict
from app.adapters.base_stt import BaseSTTAdapter
from app.adapters.mock_stt import MockSTTAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)


class WhisperSTTAdapter(BaseSTTAdapter):
    def __init__(self):
        self.fallback = MockSTTAdapter()
        self.api_key = settings.OPENAI_API_KEY

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        if not self.api_key:
            return self.fallback.transcribe(audio_path)

        try:
            import httpx
            with open(audio_path, "rb") as f:
                files = {"file": f}
                data = {"model": "whisper-1"}
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = httpx.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=30.0,
                )
                if response.status_code == 200:
                    res_json = response.json()
                    text = res_json.get("text", "")
                    return {
                        "transcript": text,
                        "confidence": 0.95,
                        "language": "en",
                        "is_uncertain": False,
                        "provider": "OpenAI-Whisper-1",
                    }
                else:
                    logger.warning("Whisper API returned %s: %s; using fallback.", response.status_code, response.text)
                    return self.fallback.transcribe(audio_path)
        except Exception as e:
            logger.error("Whisper transcription failed (%s); using fallback.", str(e))
            return self.fallback.transcribe(audio_path)
