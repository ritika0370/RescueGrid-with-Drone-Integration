"""
YOLOv8 Computer Vision Adapter.
Uses Ultralytics YOLOv8 if installed; falls back to SimulatedVisionAdapter if weights/packages are absent.
"""
import logging
from typing import Any, Dict
from app.adapters.base_vision import BaseVisionAdapter
from app.adapters.simulated_vision import SimulatedVisionAdapter

logger = logging.getLogger(__name__)


class YOLOv8VisionAdapter(BaseVisionAdapter):
    def __init__(self, model_path: str = "yolov8n.pt"):
        self.model_path = model_path
        self.model = None
        self.fallback = SimulatedVisionAdapter()
        try:
            from ultralytics import YOLO
            self.model = YOLO(model_path)
            logger.info("YOLOv8 model loaded successfully.")
        except Exception as e:
            logger.warning("Ultralytics YOLOv8 not available (%s); using simulated vision adapter fallback.", str(e))

    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        if not self.model:
            return self.fallback.analyze_image(image_path)

        try:
            results = self.model(image_path)
            detections = []
            possible_humans = 0
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    name = self.model.names[cls_id]
                    conf = float(box.conf[0])
                    coords = [int(x) for x in box.xyxy[0].tolist()]
                    if name == "person":
                        possible_humans += 1
                    detections.append({
                        "object_name": name,
                        "category": "detected_object",
                        "confidence": round(conf, 3),
                        "bbox": coords,
                        "verified": False,
                        "note": f"YOLO detected {name}. Physical safety status unverified by vision alone.",
                    })
            return {
                "model_name": f"YOLOv8-{self.model_path}",
                "detections": detections,
                "hazards_detected": [d["object_name"] for d in detections if d["object_name"] in ["fire", "car", "truck"]],
                "possible_human_count": possible_humans,
                "structural_damage_detected": any(d["object_name"] in ["debris", "damage"] for d in detections),
                "flood_detected": any(d["object_name"] in ["water", "boat"] for d in detections),
                "fire_detected": any(d["object_name"] == "fire" for d in detections),
                "smoke_detected": any(d["object_name"] == "smoke" for d in detections),
                "disclaimer": "AI detection is advisory. Human verification required before rescue deployment.",
            }
        except Exception as e:
            logger.error("Error executing YOLOv8 inference: %s; falling back to simulation.", str(e))
            return self.fallback.analyze_image(image_path)
