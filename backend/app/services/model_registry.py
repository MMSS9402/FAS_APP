from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import yaml

from app.adapters.cvpr2024_general import Cvpr2024GeneralAdapter
from app.adapters.biometric_ai_lab import BiometricAiLabAdapter
from app.adapters.iadg_cvpr2023 import IadgCvpr2023Adapter
from app.adapters.mock_models import Mock3DMaskAdapter
from app.adapters.stdn_eccv2020 import StdnEccv2020Adapter


CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "models.yaml"


class ModelRegistry:
    def __init__(self, models: List[Dict[str, Any]]) -> None:
        self._models = models
        self._models_by_id = {model["model_id"]: model for model in models}

    def list_models(self) -> List[Dict[str, Any]]:
        return list(self._models)

    def get_model(self, model_id: str) -> Dict[str, Any]:
        if model_id not in self._models_by_id:
            raise KeyError(f"Unknown model_id: {model_id}")
        return self._models_by_id[model_id]

    def get_ready_model_ids(self) -> List[str]:
        return [model["model_id"] for model in self._models if model["ready_status"] == "ready"]

    def build_adapter(self, model_id: str):
        model = self.get_model(model_id)
        implementation = model.get("implementation_status")

        if implementation == "actual" and model_id == "biometric_lab_transformer":
            adapter = BiometricAiLabAdapter(model)
        elif implementation == "actual" and model_id == "cvpr2024_mobilenet_v3_small":
            adapter = Cvpr2024GeneralAdapter(model)
        elif implementation == "actual" and model_id == "stdn_eccv2020":
            adapter = StdnEccv2020Adapter(model)
        elif implementation == "actual" and model_id == "iadg_cvpr2023":
            adapter = IadgCvpr2023Adapter(model)
        else:
            adapter = Mock3DMaskAdapter(model)

        adapter.load()
        return adapter


@lru_cache(maxsize=1)
def get_registry() -> ModelRegistry:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    models = raw.get("models", [])
    return ModelRegistry(models=models)
