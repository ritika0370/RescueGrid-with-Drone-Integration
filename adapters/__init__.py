"""
Adapters package export.
"""
from app.adapters.base_vision import BaseVisionAdapter
from app.adapters.simulated_vision import SimulatedVisionAdapter
from app.adapters.yolo_vision import YOLOv8VisionAdapter
from app.adapters.base_stt import BaseSTTAdapter
from app.adapters.mock_stt import MockSTTAdapter
from app.adapters.whisper_stt import WhisperSTTAdapter
from app.adapters.storage_adapter import StorageAdapter
from app.core.config import settings


def get_vision_adapter() -> BaseVisionAdapter:
    if settings.VISION_PROVIDER == "yolov8":
        return YOLOv8VisionAdapter(settings.YOLO_MODEL_PATH)
    return SimulatedVisionAdapter()


def get_stt_adapter() -> BaseSTTAdapter:
    if settings.STT_PROVIDER == "whisper":
        return WhisperSTTAdapter()
    return MockSTTAdapter()


__all__ = [
    "BaseVisionAdapter",
    "SimulatedVisionAdapter",
    "YOLOv8VisionAdapter",
    "BaseSTTAdapter",
    "MockSTTAdapter",
    "WhisperSTTAdapter",
    "StorageAdapter",
    "get_vision_adapter",
    "get_stt_adapter",
]
