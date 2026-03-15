from __future__ import annotations


def attack_track_label(attack_track: str) -> str:
    if attack_track == "3d_specialized":
        return "3D 마스크 특화 FAS"

    if attack_track == "general_physical_digital_fas":
        return "일반 FAS (물리·디지털 공격)"

    return attack_track


def ready_status_label(ready_status: str) -> str:
    if ready_status == "ready":
        return "즉시 실행 가능"

    if ready_status == "research_only":
        return "연구용"

    if ready_status == "video_only":
        return "비디오 전용"

    return ready_status


def implementation_status_label(implementation_status: str) -> str:
    if implementation_status == "actual":
        return "실제 체크포인트"

    if implementation_status == "mock":
        return "모의 결과"

    if implementation_status == "planned":
        return "미연동"

    return implementation_status
