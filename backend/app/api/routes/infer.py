from __future__ import annotations

import json
import uuid
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.schemas.infer import InferResponse
from app.services.inference_runner import InferenceRunner
from app.services.model_labels import attack_track_label
from app.services.model_registry import get_registry


router = APIRouter(prefix="/api/infer", tags=["infer"])


@router.post("", response_model=InferResponse)
async def infer_images(
    files: List[UploadFile] = File(...),
    selected_models: str = Form("[]"),
    use_all_models: bool = Form(False),
) -> InferResponse:
    registry = get_registry()
    runner = InferenceRunner(registry)

    try:
        selected_model_ids = json.loads(selected_models)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="selected_models must be a JSON array") from exc

    if not isinstance(selected_model_ids, list):
        raise HTTPException(status_code=400, detail="selected_models must be a JSON array")

    resolved_models = runner.resolve_model_ids(selected_model_ids, use_all_models)
    if not resolved_models:
        raise HTTPException(status_code=400, detail="No runnable models were selected")

    image_results = []
    success_count = 0
    failure_count = 0
    total_elapsed = 0
    total_runs = 0

    for upload in files:
        try:
            payload = await upload.read()
            image = Image.open(io_from_bytes(payload)).convert("RGB")
        except UnidentifiedImageError as exc:
            raise HTTPException(status_code=400, detail=f"Unsupported image file: {upload.filename}") from exc

        result = runner.run_for_image(image=image, image_name=upload.filename, model_ids=resolved_models)
        image_results.append(result)

        for row in result["results"]:
            total_runs += 1
            total_elapsed += row["inference_time_ms"]
            if row["status"] == "success":
                success_count += 1
            else:
                failure_count += 1

    summary = {
        "image_count": len(image_results),
        "model_count": len(resolved_models),
        "successful_runs": success_count,
        "failed_runs": failure_count,
        "average_inference_time_ms": round(total_elapsed / total_runs, 2) if total_runs else 0,
    }

    resolved_configs = [registry.get_model(model_id) for model_id in resolved_models]
    actual_models = [model["display_name"] for model in resolved_configs if model.get("implementation_status") == "actual"]
    attack_tracks = sorted({attack_track_label(model["attack_track"]) for model in resolved_configs})

    notes = [
        f"이번 실행의 대상 트랙: {', '.join(attack_tracks)}",
        "All Models는 현재 ready 상태 모델 전체를 실행합니다.",
    ]
    if actual_models:
        notes.append(f"실제 체크포인트로 실행된 모델: {', '.join(actual_models)}")
    if "biometric_lab_transformer" in resolved_models:
        notes.append("Biometric Lab Transformer는 시계열 기반 공개 구현이라 단일 이미지 입력 시 프레임 복제 방식으로 동작합니다.")
    if "cvpr2024_mobilenet_v3_small" in resolved_models:
        notes.append("CVPR2024 MobileNetV3 Small은 3D 마스크 전용이 아니라 일반 FAS (물리·디지털 공격) 모델입니다.")
    notes.append("모델별 원본 전처리는 통일하지 않고, 결과에 적용 전처리 메타데이터를 함께 표시합니다.")

    return InferResponse(
        request_id=f"req_{uuid.uuid4().hex[:12]}",
        resolved_models=resolved_models,
        summary=summary,
        images=image_results,
        notes=notes,
    )


def io_from_bytes(payload: bytes):
    from io import BytesIO

    return BytesIO(payload)
