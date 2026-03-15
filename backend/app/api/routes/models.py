from __future__ import annotations

from typing import List

from fastapi import APIRouter

from app.schemas.infer import ModelMetadata
from app.services.model_labels import (
    attack_track_label,
    implementation_status_label,
    ready_status_label,
)
from app.services.model_registry import get_registry


router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=List[ModelMetadata])
def list_models() -> List[ModelMetadata]:
    registry = get_registry()
    response = []
    for model in registry.list_models():
        enriched = {
            **model,
            "track_label": attack_track_label(model["attack_track"]),
            "ready_status_label": ready_status_label(model["ready_status"]),
            "implementation_status_label": implementation_status_label(
                model.get("implementation_status", "unknown")
            ),
        }
        response.append(ModelMetadata(**enriched))
    return response
