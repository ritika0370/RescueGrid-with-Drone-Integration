"""
Abstract Base Class for Computer Vision Object Detection Models.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseVisionAdapter(ABC):
    @abstractmethod
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze an image file and detect relevant disaster hazards/objects.
        Returns a dictionary with:
        - detections: List[Dict] with object_name, confidence, bbox, category
        - hazards_detected: List[str]
        - possible_human_count: int
        - structural_damage_detected: bool
        - flood_detected: bool
        - fire_detected: bool
        """
        pass
