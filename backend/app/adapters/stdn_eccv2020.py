from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict

from PIL import Image

from .base import BaseFASAdapter


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]
RUNNER_PATH = Path(__file__).resolve().parents[1] / "external" / "stdn_subprocess_runner.py"
DEFAULT_REPO_DIR = PROJECT_ROOT / "third_party" / "ECCV20-STDN"
DEFAULT_CHECKPOINT_DIR = BACKEND_DIR / "assets" / "stdn_eccv2020"


class StdnEccv2020Adapter(BaseFASAdapter):
    def load(self) -> None:
        runtime = self.config.get("runtime", {})
        self._python_bin_env = runtime.get("python_bin_env", "STDN_PYTHON_BIN")
        self._repo_dir = self._resolve_path(runtime.get("repo_dir"), DEFAULT_REPO_DIR)
        self._checkpoint_dir = self._resolve_path(runtime.get("checkpoint_dir"), DEFAULT_CHECKPOINT_DIR)
        self._runner_script = self._resolve_path(runtime.get("runner_script"), RUNNER_PATH)

    def predict(self, image: Image.Image) -> Dict[str, Any]:
        python_bin = os.environ.get(self._python_bin_env)
        if not python_bin:
            raise RuntimeError(
                f"STDN external runtime is not configured. Set environment variable {self._python_bin_env} "
                "to a Python binary that can run TensorFlow-compatible STDN inference."
            )

        if not self._repo_dir.exists():
            raise RuntimeError(
                f"STDN repository not found at {self._repo_dir}. Clone the official repository first."
            )

        if not self._checkpoint_dir.exists():
            raise RuntimeError(
                f"STDN checkpoint directory not found at {self._checkpoint_dir}. "
                "Copy ckpt-50 files before running this model."
            )

        preprocessed, crop_meta = self._prepare_image(image)

        with tempfile.TemporaryDirectory(prefix="stdn_infer_") as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "input.png"
            output_path = temp_path / "output.json"
            preprocessed.save(input_path)

            command = [
                python_bin,
                str(self._runner_script),
                "--repo-dir",
                str(self._repo_dir),
                "--checkpoint-dir",
                str(self._checkpoint_dir),
                "--input-image",
                str(input_path),
                "--output-json",
                str(output_path),
            ]

            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=180,
            )
            if completed.returncode != 0:
                detail = completed.stderr.strip() or completed.stdout.strip() or "unknown STDN runner error"
                raise RuntimeError(f"STDN subprocess inference failed: {detail}")

            payload = json.loads(output_path.read_text(encoding="utf-8"))

        features = dict(payload.get("features", {}))
        features.update(
            {
                "crop_detector": crop_meta["detector"],
                "crop_box": crop_meta["crop_box"],
                "score_source": payload.get("score_source", "M"),
            }
        )
        note = payload.get(
            "score_direction_note",
            "STDN M output is treated as spoof-direction logit based on bundled live/spoof sample validation.",
        )

        return {
            "raw_score": float(payload["raw_score"]),
            "features": features,
            "preprocessing_note": f"{self._format_preprocessing(crop_meta)}, score_note={note}",
            "preprocessing": self.config.get("preprocessing", {}),
        }

    def _prepare_image(self, image: Image.Image) -> tuple[Image.Image, Dict[str, str]]:
        return image.convert("RGB"), {
            "detector": "user_supplied_face_crop",
            "crop_box": "user_supplied",
        }

    def _format_preprocessing(self, crop_meta: Dict[str, str]) -> str:
        prep = self.config.get("preprocessing", {})
        return ", ".join(
            [
                f"detector={crop_meta['detector']}",
                f"crop={prep.get('crop_strategy', 'n/a')}",
                f"crop_box={crop_meta['crop_box']}",
                f"size={prep.get('input_size', 'n/a')}",
                f"norm={prep.get('normalization_scheme', 'n/a')}",
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
