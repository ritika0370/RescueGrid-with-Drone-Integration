"""
Simulated Computer Vision Model Adapter.
Provides deterministic, safety-compliant disaster object detection
for testing, demos, and environments without GPU/YOLO weights.
Adheres strictly to the rule: "Do not claim that a person is trapped merely
because a model detects a human-shaped object."
"""
import os
from typing import Any, Dict, List
from PIL import Image, ImageStat
from app.adapters.base_vision import BaseVisionAdapter


class SimulatedVisionAdapter(BaseVisionAdapter):
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze an image, extracting visual indicators of hazards.
        """
        detections: List[Dict[str, Any]] = []
        hazards: List[str] = []
        possible_humans = 0
        structural_damage = False
        flood_water = False
        fire = False
        smoke = False

        filename = os.path.basename(image_path).lower()

        # Extract basic image statistics if file exists
        if os.path.exists(image_path):
            try:
                with Image.open(image_path) as img:
                    width, height = img.size
                    stat = ImageStat.Stat(img)
                    raw_mean = list(stat.mean[:3])
                    mean_colors = raw_mean + [128] * (3 - len(raw_mean))
            except Exception:
                width, height = 1920, 1080
                mean_colors = [128, 128, 128]
        else:
            width, height = 1920, 1080
            mean_colors = [128, 128, 128]

        # Deterministic detection heuristics based on filename, visual context, or seed tags
        if "flood" in filename or "water" in filename or (mean_colors[2] > mean_colors[0] + 20):
            flood_water = True
            hazards.append("Floodwater inundation detected across surface")
            detections.append({
                "object_name": "floodwater",
                "category": "hazard",
                "confidence": 0.91,
                "bbox": [0, int(height * 0.4), width, height],
                "verified": False,
                "note": "AI-detected possible water accumulation.",
            })

        if "fire" in filename or "flame" in filename or (mean_colors[0] > 180 and mean_colors[2] < 100):
            fire = True
            smoke = True
            hazards.append("Active flame and thermal signature detected")
            detections.append({
                "object_name": "fire",
                "category": "hazard",
                "confidence": 0.94,
                "bbox": [int(width * 0.2), int(height * 0.2), int(width * 0.8), int(height * 0.7)],
                "verified": False,
                "note": "AI-detected possible fire.",
            })

        if "smoke" in filename:
            smoke = True
            hazards.append("Dense smoke plume visible")
            detections.append({
                "object_name": "smoke",
                "category": "hazard",
                "confidence": 0.88,
                "bbox": [int(width * 0.1), 0, int(width * 0.9), int(height * 0.5)],
                "verified": False,
                "note": "AI-detected possible smoke.",
            })

        if "collapse" in filename or "damage" in filename or "debris" in filename:
            structural_damage = True
            hazards.append("Structural failure or structural debris visible")
            detections.append({
                "object_name": "damaged_structure",
                "category": "hazard",
                "confidence": 0.87,
                "bbox": [int(width * 0.15), int(height * 0.3), int(width * 0.85), int(height * 0.9)],
                "verified": False,
                "note": "AI-detected possible structural damage.",
            })

        if "person" in filename or "people" in filename or "victim" in filename or "stranded" in filename:
            possible_humans = 2
            detections.append({
                "object_name": "person",
                "category": "human_detection",
                "confidence": 0.84,
                "bbox": [int(width * 0.4), int(height * 0.5), int(width * 0.5), int(height * 0.75)],
                "verified": False,
                "note": "AI-detected human-shaped silhouette. Status (trapped vs safe) UNVERIFIED by vision alone.",
            })
            detections.append({
                "object_name": "person",
                "category": "human_detection",
                "confidence": 0.79,
                "bbox": [int(width * 0.55), int(height * 0.52), int(width * 0.62), int(height * 0.76)],
                "verified": False,
                "note": "AI-detected human-shaped silhouette. Status UNVERIFIED.",
            })

        # Default fallback detection if no specific keyword matched
        if not detections:
            detections.append({
                "object_name": "outdoor_terrain",
                "category": "environment",
                "confidence": 0.95,
                "bbox": [0, 0, width, height],
                "verified": False,
                "note": "Visual scan complete. No critical structural collapse or flame detected in frame.",
            })

        return {
            "model_name": "SimulatedVisionAdapter-v1",
            "detections": detections,
            "hazards_detected": hazards,
            "possible_human_count": possible_humans,
            "structural_damage_detected": structural_damage,
            "flood_detected": flood_water,
            "fire_detected": fire,
            "smoke_detected": smoke,
            "disclaimer": "AI detection is advisory. Human verification required before rescue deployment.",
        }
