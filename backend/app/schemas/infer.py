from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ModelMetadata(BaseModel):
    model_id: str
    display_name: str
    paper_title: str
    paper_year: int
    paper_type: str
    repository_url: str
    weights_source: str
    attack_track: str
    input_type: str
    ready_status: str
    implementation_status: str
    score_semantics: str
    threshold_default: float
    preprocessing: Dict[str, Any]
    track_label: Optional[str] = None
    ready_status_label: Optional[str] = None
    implementation_status_label: Optional[str] = None


class PredictionResult(BaseModel):
    model_id: str
    display_name: str
    paper_title: str
    paper_year: int
    attack_track: str
    prediction_label: Optional[str]
    raw_score: Optional[float]
    normalized_spoof_score: Optional[float]
    threshold: float
    inference_time_ms: int
    status: str
    implementation_status: str
    ready_status: str
    preprocessing_note: str
    preprocessing: Dict[str, Any]
    features: Dict[str, Any]
    raw_score_meaning: str
    normalized_score_meaning: str
    threshold_rule: str
    track_label: Optional[str] = None
    implementation_status_label: Optional[str] = None
    message: Optional[str] = None


class ImageInferenceResult(BaseModel):
    image_name: str
    results: List[PredictionResult]


class InferResponse(BaseModel):
    request_id: str
    resolved_models: List[str]
    summary: Dict[str, Any]
    images: List[ImageInferenceResult]
    notes: List[str]
