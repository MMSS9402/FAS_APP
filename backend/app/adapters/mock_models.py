from __future__ import annotations

import math
from typing import Any, Dict

from PIL import Image, ImageFilter, ImageOps, ImageStat

from .base import BaseFASAdapter


class Mock3DMaskAdapter(BaseFASAdapter):
    """Deterministic placeholder adapter until real checkpoints are wired."""

    def load(self) -> None:
        return

    def predict(self, image: Image.Image) -> Dict[str, Any]:
        grayscale = ImageOps.grayscale(image)
        resized = grayscale.resize((128, 128))
        edges = resized.filter(ImageFilter.FIND_EDGES)

        brightness = (ImageStat.Stat(resized).mean[0]) / 255.0
        contrast = (ImageStat.Stat(resized).stddev[0]) / 64.0
        edge_density = (ImageStat.Stat(edges).mean[0]) / 255.0

        profile = self.config.get("score_profile", {})
        raw_base = (
            contrast * float(profile.get("contrast_weight", 0.4))
            + edge_density * float(profile.get("edge_weight", 0.4))
            + (1.0 - brightness) * float(profile.get("brightness_weight", 0.2))
            + float(profile.get("bias", 0.0))
        )

        semantics = self.score_semantics
        if semantics == "spoof_probability":
            raw_score = max(0.0, min(1.0, raw_base))
        elif semantics == "real_probability":
            raw_score = max(0.0, min(1.0, 1.0 - raw_base))
        elif semantics == "logit_spoof":
            clipped = max(0.01, min(0.99, raw_base))
            raw_score = math.log(clipped / (1.0 - clipped))
        else:
            raw_score = raw_base

        return {
            "raw_score": raw_score,
            "features": {
                "brightness": round(brightness, 4),
                "contrast": round(contrast, 4),
                "edge_density": round(edge_density, 4),
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
            ]
        )
