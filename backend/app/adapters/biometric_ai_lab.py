from __future__ import annotations

import importlib.util
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import cv2
import numpy as np
from PIL import Image

from .base import BaseFASAdapter


ASSET_DIR = Path(__file__).resolve().parents[2] / "assets" / "biometric_ai_lab"
INFERENCE_PATH = ASSET_DIR / "inference.py"
MODEL_PATH = ASSET_DIR / "antispoofing_full.pth"
YOLO_PATH = ASSET_DIR / "yolov8s-face-lindevs.onnx"


class BiometricAiLabAdapter(BaseFASAdapter):
    def load(self) -> None:
        self._detector = get_detector(self.threshold)

    def predict(self, image: Image.Image) -> Dict[str, Any]:
        rgb = np.array(image)
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        result = self._detector.predict_image(bgr)

        bbox = result.get("bbox")
        bbox_text = "none"
        if bbox:
            bbox_text = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"

        return {
            "raw_score": float(result.get("confidence", 0.0)),
            "features": {
                "bbox": bbox_text,
                "prediction": result.get("prediction"),
                "is_attack": result.get("is_attack"),
            },
            "preprocessing_note": self._format_preprocessing(),
            "preprocessing": self.config.get("preprocessing", {}),
        }

    def _format_preprocessing(self) -> str:
        prep = self.config.get("preprocessing", {})
        return ", ".join(
            [
                f"detector={prep.get('face_detector', 'n/a')}",
                f"crop={prep.get('crop_strategy', 'n/a')}",
                f"size={prep.get('input_size', 'n/a')}",
                f"norm={prep.get('normalization_scheme', 'n/a')}",
                "sequence=single_image_duplication",
            ]
        )


@lru_cache(maxsize=1)
def load_inference_module():
    spec = importlib.util.spec_from_file_location("biometric_ai_lab_inference", INFERENCE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load inference module from {INFERENCE_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=2)
def get_detector(threshold: float):
    module = load_inference_module()
    detector = module.AntiSpoofingDetector(
        model_path=str(MODEL_PATH),
        yolo_model_path=str(YOLO_PATH),
        device="cpu",
        num_frames=10,
        threshold=float(threshold),
    )
    return detector
