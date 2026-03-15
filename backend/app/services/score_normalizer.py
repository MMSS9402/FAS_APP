from __future__ import annotations

import math


def normalize_to_spoof_probability(raw_score: float, score_semantics: str) -> float:
    if score_semantics == "spoof_probability":
        return _clamp(raw_score)

    if score_semantics == "spoof_probability_candidate":
        return _clamp(raw_score)

    if score_semantics == "real_probability":
        return _clamp(1.0 - raw_score)

    if score_semantics == "logit_spoof":
        return _clamp(1.0 / (1.0 + math.exp(-raw_score)))

    return _clamp(raw_score)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def describe_raw_score_semantics(score_semantics: str) -> str:
    if score_semantics == "spoof_probability":
        return "Raw Score가 높을수록 FAKE 가능성이 높습니다."

    if score_semantics == "spoof_probability_candidate":
        return "Raw Score는 임시 spoof 기준 점수로 해석 중이며, 현재는 높을수록 FAKE라고 가정합니다."

    if score_semantics == "real_probability":
        return "Raw Score가 높을수록 REAL 가능성이 높습니다."

    if score_semantics == "logit_spoof":
        return "Raw Score는 spoof logit이며, 높을수록 FAKE 방향입니다."

    return "Raw Score 해석 규칙이 고정되지 않았습니다."


def describe_normalized_score() -> str:
    return "Norm Score는 0~1 spoof 기준 점수이며, 높을수록 FAKE 가능성이 높습니다."


def describe_threshold_rule(threshold: float) -> str:
    return f"Norm Score가 {threshold:.4f} 이상이면 FAKE, 미만이면 REAL로 판정합니다."
