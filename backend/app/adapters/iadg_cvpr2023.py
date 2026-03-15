from __future__ import annotations

import importlib
import sys
import types
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import cv2
import numpy as np
import torch
from omegaconf import OmegaConf
from PIL import Image

from .base import BaseFASAdapter


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_REPO_DIR = PROJECT_ROOT / "third_party" / "IADG"
DEFAULT_CHECKPOINT_PATH = BACKEND_DIR / "assets" / "iadg" / "OCI2M" / "model_best.pth.tar"
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "third_party" / "IADG" / "configs" / "OCI2M_test.yaml"


class IadgCvpr2023Adapter(BaseFASAdapter):
    def load(self) -> None:
        runtime = self.config.get("runtime", {})
        self._repo_dir = self._resolve_path(runtime.get("repo_dir"), DEFAULT_REPO_DIR)
        self._checkpoint_path = self._resolve_path(runtime.get("checkpoint_path"), DEFAULT_CHECKPOINT_PATH)
        self._config_path = self._resolve_path(runtime.get("config_path"), DEFAULT_CONFIG_PATH)
        self._device = torch.device("cpu")
        self._face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self._model, self._iadg_config = get_iadg_model(
            repo_dir=self._repo_dir,
            checkpoint_path=self._checkpoint_path,
            config_path=self._config_path,
        )

    def predict(self, image: Image.Image) -> Dict[str, Any]:
        cropped, crop_meta = self._prepare_image(image)
        tensor = self._to_tensor(cropped).to(self._device)
        dummy_label = torch.zeros((1,), dtype=torch.long, device=self._device)

        with torch.no_grad():
            outputs_catcls, outputs_catdepth, _, _, _, _ = self._model(
                tensor,
                dummy_label,
                apply_shade=True,
                cal_covstat=False,
                apply_wt=False,
            )
            real_cls_prob = torch.softmax(outputs_catcls["out"], dim=1)[:, 0]
            depth_realness = outputs_catdepth["out"].reshape(outputs_catdepth["out"].shape[0], -1).mean(dim=1)
            raw_real_score = float((real_cls_prob + depth_realness)[0].cpu())

        official_raw_threshold = float(getattr(self._iadg_config, "official_raw_threshold", 0.16627258561550506))
        return {
            "raw_score": raw_real_score,
            "features": {
                "real_class_probability": round(float(real_cls_prob[0].cpu()), 6),
                "depth_realness_mean": round(float(depth_realness[0].cpu()), 6),
                "raw_real_score": round(raw_real_score, 6),
                "official_raw_threshold": round(official_raw_threshold, 6),
                "checkpoint_path": str(self._checkpoint_path),
                "crop_detector": crop_meta["detector"],
                "crop_box": crop_meta["crop_box"],
            },
            "preprocessing_note": self._format_preprocessing(crop_meta, official_raw_threshold),
            "preprocessing": self.config.get("preprocessing", {}),
        }

    def _prepare_image(self, image: Image.Image) -> tuple[np.ndarray, Dict[str, str]]:
        rgb = np.asarray(image.convert("RGB"))
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

        detector_name = "center_crop_fallback"
        if not self._face_cascade.empty():
            faces = self._face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(80, 80),
            )
        else:
            faces = ()

        if len(faces):
            x, y, w, h = max(faces, key=lambda face: face[2] * face[3])
            detector_name = "opencv_haar"
            x1, y1, x2, y2 = self._square_with_margin(
                x=x,
                y=y,
                w=w,
                h=h,
                width=rgb.shape[1],
                height=rgb.shape[0],
            )
        else:
            side = min(rgb.shape[0], rgb.shape[1])
            x1 = max((rgb.shape[1] - side) // 2, 0)
            y1 = max((rgb.shape[0] - side) // 2, 0)
            x2 = x1 + side
            y2 = y1 + side

        cropped = rgb[y1:y2, x1:x2]
        return cropped, {
            "detector": detector_name,
            "crop_box": f"{x1},{y1},{x2},{y2}",
        }

    def _square_with_margin(
        self,
        *,
        x: int,
        y: int,
        w: int,
        h: int,
        width: int,
        height: int,
    ) -> tuple[int, int, int, int]:
        margin = float(self.config.get("preprocessing", {}).get("service_margin", 0.3))
        side = max(w, h)
        padded = int(round(side * (1.0 + margin)))
        center_x = x + (w / 2.0)
        center_y = y + (h / 2.0)

        x1 = max(int(round(center_x - padded / 2.0)), 0)
        y1 = max(int(round(center_y - padded / 2.0)), 0)
        x2 = min(x1 + padded, width)
        y2 = min(y1 + padded, height)

        final_side = min(x2 - x1, y2 - y1)
        x2 = x1 + final_side
        y2 = y1 + final_side
        return x1, y1, x2, y2

    def _to_tensor(self, rgb_image: np.ndarray) -> torch.Tensor:
        transform = self._iadg_config.transform
        resized = cv2.resize(rgb_image, (transform.image_size, transform.image_size), interpolation=cv2.INTER_LINEAR)
        array = resized.astype(np.float32) / 255.0
        mean = np.asarray(transform.mean, dtype=np.float32)
        std = np.asarray(transform.std, dtype=np.float32)
        normalized = (array - mean) / std
        tensor = torch.from_numpy(normalized).permute(2, 0, 1).unsqueeze(0).float()
        return tensor

    def _format_preprocessing(self, crop_meta: Dict[str, str], official_raw_threshold: float) -> str:
        prep = self.config.get("preprocessing", {})
        return ", ".join(
            [
                f"detector={crop_meta['detector']}",
                f"crop={prep.get('crop_strategy', 'n/a')}",
                f"crop_box={crop_meta['crop_box']}",
                f"size={prep.get('input_size', 'n/a')}",
                f"norm={prep.get('normalization_scheme', 'n/a')}",
                "official_config=OCI2M_test.yaml",
                f"official_raw_threshold={official_raw_threshold:.6f}",
            ]
        )

    @staticmethod
    def _resolve_path(raw_value: str | None, default: Path) -> Path:
        if raw_value:
            path = Path(raw_value)
            if not path.is_absolute():
                path = PROJECT_ROOT / path
            return path
        return default


@lru_cache(maxsize=2)
def get_iadg_model(repo_dir: Path, checkpoint_path: Path, config_path: Path):
    if str(repo_dir) not in sys.path:
        sys.path.insert(0, str(repo_dir))

    importlib.invalidate_caches()
    for module_name in ("utils", "models", "dataloaders", "losses"):
        loaded = sys.modules.get(module_name)
        if loaded is None:
            continue
        module_file = str(getattr(loaded, "__file__", ""))
        if module_file and not module_file.startswith(str(repo_dir)):
            del sys.modules[module_name]

    utils_package = types.ModuleType("utils")
    utils_package.__path__ = [str((repo_dir / "utils").resolve())]
    sys.modules["utils"] = utils_package

    models_module = importlib.import_module("models")
    config = OmegaConf.load(config_path)
    config.official_raw_threshold = 0.16627258561550506

    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model_name = config.model.name
    model_params = config.model.params
    model = models_module.__dict__[model_name](**model_params)

    state_dict = checkpoint["state_dict"] if "state_dict" in checkpoint else checkpoint
    cleaned = {}
    for key, value in state_dict.items():
        if key.startswith("module."):
            cleaned[key[len("module."):]] = value
        else:
            cleaned[key] = value

    model.load_state_dict(cleaned, strict=True)
    model.eval()
    return model, config
