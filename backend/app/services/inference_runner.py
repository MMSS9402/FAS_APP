from __future__ import annotations

import time
from typing import Any, Dict, List

from PIL import Image

from app.services.model_registry import ModelRegistry
from app.services.model_labels import attack_track_label, implementation_status_label
from app.services.score_normalizer import (
    describe_normalized_score,
    describe_raw_score_semantics,
    describe_threshold_rule,
    normalize_to_spoof_probability,
)


class InferenceRunner:
    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry

    def resolve_model_ids(self, selected_models: List[str], use_all_models: bool) -> List[str]:
        if use_all_models:
            return self.registry.get_ready_model_ids()
        return selected_models

    def run_for_image(self, image: Image.Image, image_name: str, model_ids: List[str]) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []

        for model_id in model_ids:
            model_config = self.registry.get_model(model_id)
            start = time.perf_counter()
            try:
                adapter = self.registry.build_adapter(model_id)
                raw = adapter.predict(image)
                raw_score = float(raw["raw_score"])
                normalized_score = normalize_to_spoof_probability(raw_score, model_config["score_semantics"])
                threshold = float(model_config["threshold_default"])
                elapsed_ms = int((time.perf_counter() - start) * 1000)

                results.append(
                    {
                        "model_id": model_id,
                        "display_name": model_config["display_name"],
                        "paper_title": model_config["paper_title"],
                        "paper_year": model_config["paper_year"],
                        "attack_track": model_config["attack_track"],
                        "prediction_label": "FAKE" if normalized_score >= threshold else "REAL",
                        "raw_score": round(raw_score, 4),
                        "normalized_spoof_score": round(normalized_score, 4),
                        "threshold": threshold,
                        "inference_time_ms": elapsed_ms,
                        "status": "success",
                        "implementation_status": model_config.get("implementation_status", "unknown"),
                        "ready_status": model_config["ready_status"],
                        "features": raw.get("features", {}),
                        "preprocessing_note": raw.get("preprocessing_note", ""),
                        "preprocessing": raw.get("preprocessing", {}),
                        "raw_score_meaning": describe_raw_score_semantics(model_config["score_semantics"]),
                        "normalized_score_meaning": describe_normalized_score(),
                        "threshold_rule": describe_threshold_rule(threshold),
                        "track_label": attack_track_label(model_config["attack_track"]),
                        "implementation_status_label": implementation_status_label(
                            model_config.get("implementation_status", "unknown")
                        ),
                    }
                )
            except Exception as exc:  # pragma: no cover - fallback path
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                results.append(
                    {
                        "model_id": model_id,
                        "display_name": model_config["display_name"],
                        "paper_title": model_config["paper_title"],
                        "paper_year": model_config["paper_year"],
                        "attack_track": model_config["attack_track"],
                        "prediction_label": None,
                        "raw_score": None,
                        "normalized_spoof_score": None,
                        "threshold": model_config["threshold_default"],
                        "inference_time_ms": elapsed_ms,
                        "status": "failed",
                        "message": str(exc),
                        "implementation_status": model_config.get("implementation_status", "unknown"),
                        "ready_status": model_config["ready_status"],
                        "features": {},
                        "preprocessing_note": "",
                        "preprocessing": model_config.get("preprocessing", {}),
                        "raw_score_meaning": describe_raw_score_semantics(model_config["score_semantics"]),
                        "normalized_score_meaning": describe_normalized_score(),
                        "threshold_rule": describe_threshold_rule(float(model_config["threshold_default"])),
                        "track_label": attack_track_label(model_config["attack_track"]),
                        "implementation_status_label": implementation_status_label(
                            model_config.get("implementation_status", "unknown")
                        ),
                    }
                )

        return {
            "image_name": image_name,
            "results": results,
        }
