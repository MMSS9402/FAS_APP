from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import cv2
import numpy as np
import torch
from PIL import Image

from .base import BaseFASAdapter


REPO_DIR = Path(__file__).resolve().parents[3] / "third_party" / "cvpr2024-face-anti-spoofing-challenge"
CHECKPOINT_PATH = Path(__file__).resolve().parents[2] / "assets" / "cvpr2024_general_fas" / "mobilenet_v3_small.pth"


class Cvpr2024GeneralAdapter(BaseFASAdapter):
    def load(self) -> None:
        self._model = get_model_instance()
        self._device = torch.device("cpu")

    def predict(self, image: Image.Image) -> Dict[str, Any]:
        rgb = np.array(image.convert("RGB"))
        resized = cv2.resize(rgb, (224, 224), interpolation=cv2.INTER_LINEAR)
        tensor = torch.from_numpy(resized).permute(2, 0, 1).float() / 255.0
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        tensor = ((tensor - mean) / std).unsqueeze(0).to(self._device)

        with torch.no_grad():
            logits = self._model(tensor)
            probs = torch.softmax(logits, dim=1)[0].cpu().numpy()

        live_prob = float(probs[0])
        spoof_prob = float(probs[1])

        return {
            "raw_score": spoof_prob,
            "features": {
                "live_probability": round(live_prob, 4),
                "spoof_probability": round(spoof_prob, 4),
                "input_mode": "full_image",
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


@lru_cache(maxsize=1)
def get_model_instance():
    if str(REPO_DIR) not in sys.path:
        sys.path.insert(0, str(REPO_DIR))

    from nets.utils import get_model  # pylint: disable=import-error

    model = get_model("mobilenet_v3_small", num_classes=2)
    checkpoint = torch.load(CHECKPOINT_PATH, map_location="cpu")

    if "state_dict_ema" in checkpoint and checkpoint["state_dict_ema"] is not None:
        state_dict = checkpoint["state_dict_ema"]
        state_dict.pop("n_averaged", None)
    elif "state_dict" in checkpoint:
        state_dict = checkpoint["state_dict"]
    else:
        state_dict = checkpoint

    cleaned = {}
    for key, value in state_dict.items():
        if key.startswith("module.module."):
            cleaned[key[len("module.module."):]] = value
        elif key.startswith("module."):
            cleaned[key[len("module."):]] = value
        else:
            cleaned[key] = value

    model.load_state_dict(cleaned, strict=True)
    model.eval()
    return model
