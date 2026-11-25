"""
Abstract Base Class for Speech-To-Text (STT) Providers.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseSTTAdapter(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio recording to text.
        Returns:
        - transcript: str
        - confidence: float
        - language: str
        - is_uncertain: bool
        """
        pass
