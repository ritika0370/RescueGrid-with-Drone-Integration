"""
Configurable Mock/Demo Speech-To-Text Adapter.
Provides deterministic transcription for testing and demo recordings,
preserving language tags and explicitly flagging uncertain or low-confidence audio.
"""
import os
from typing import Any, Dict
from app.adapters.base_stt import BaseSTTAdapter


class MockSTTAdapter(BaseSTTAdapter):
    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        filename = os.path.basename(audio_path).lower()
        
        # Check if an explicit transcript text file exists alongside audio
        txt_path = os.path.splitext(audio_path)[0] + ".txt"
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return {
                    "transcript": content,
                    "confidence": 0.96,
                    "language": "en",
                    "is_uncertain": False,
                    "provider": "ConfigurableSTT-FileReader",
                }

        # Deterministic simulation based on emergency keywords
        if "flood" in filename or "water" in filename:
            return {
                "transcript": "Emergency! The flood water is rising rapidly past the ground floor. Two elderly residents are stranded on the terrace. Please send a rescue boat immediately!",
                "confidence": 0.92,
                "language": "en",
                "is_uncertain": False,
                "provider": "ConfigurableSTT-Demo",
            }
        elif "fire" in filename or "smoke" in filename:
            return {
                "transcript": "There is a massive fire on the third floor! Smoke is filling the stairwell and we cannot breathe. Please dispatch firefighters!",
                "confidence": 0.94,
                "language": "en",
                "is_uncertain": False,
                "provider": "ConfigurableSTT-Demo",
            }
        elif "unclear" in filename or "static" in filename or "noisy" in filename:
            return {
                "transcript": "[Heavy static] ...trapped under... [indistinct] ...water rising... please help...",
                "confidence": 0.38,
                "language": "en",
                "is_uncertain": True,
                "provider": "ConfigurableSTT-Demo",
            }
        else:
            return {
                "transcript": "Emergency reported at this location. Citizen urgently requesting rescue assistance and evacuation support.",
                "confidence": 0.85,
                "language": "en",
                "is_uncertain": False,
                "provider": "ConfigurableSTT-Demo",
            }
