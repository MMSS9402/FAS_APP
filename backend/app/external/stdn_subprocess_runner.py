from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run STDN inference in external runtime.")
    parser.add_argument("--repo-dir", required=True, help="Path to cloned ECCV20-STDN repository")
    parser.add_argument("--checkpoint-dir", required=True, help="Directory containing STDN checkpoint files")
    parser.add_argument("--input-image", required=True, help="Preprocessed image path")
    parser.add_argument("--output-json", required=True, help="Path to write inference result json")
    return parser.parse_args()


def import_tensorflow():
    try:
        import tensorflow as tf  # type: ignore
    except Exception as exc:  # pragma: no cover - runtime specific
        raise RuntimeError(
            "TensorFlow compatible runtime is not available. "
            "Use a separate STDN environment and set STDN_PYTHON_BIN."
        ) from exc

    if hasattr(tf, "disable_v2_behavior"):
        tf.disable_v2_behavior()
    return tf


def resolve_checkpoint_prefix(checkpoint_dir: Path) -> Path:
    checkpoint_file = checkpoint_dir / "checkpoint"
    if checkpoint_file.exists():
        text = checkpoint_file.read_text(encoding="utf-8")
        match = re.search(r'model_checkpoint_path:\s+"([^"]+)"', text)
        if match:
            return checkpoint_dir / match.group(1)

    index_files = sorted(checkpoint_dir.glob("*.index"))
    if index_files:
        return index_files[-1].with_suffix("")

    raise FileNotFoundError(f"No TensorFlow checkpoint found in {checkpoint_dir}")


def prepare_workspace(repo_dir: Path, checkpoint_dir: Path, input_image: Path) -> tuple[Path, Path]:
    workspace_root = Path(tempfile.mkdtemp(prefix="stdn_official_"))
    workspace_repo = workspace_root / "ECCV20-STDN"

    shutil.copytree(
        repo_dir,
        workspace_repo,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "data", "log"),
    )

    live_dir = workspace_repo / "data" / "test" / "live" / "request_0001"
    spoof_dir = workspace_repo / "data" / "test" / "spoof"
    live_dir.mkdir(parents=True, exist_ok=True)
    spoof_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(input_image, live_dir / input_image.name)

    log_dir = workspace_repo / "log" / "STDN"
    test_dir = log_dir / "test"
    log_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)

    for checkpoint_file in checkpoint_dir.iterdir():
        if checkpoint_file.is_file():
            shutil.copy2(checkpoint_file, log_dir / checkpoint_file.name)

    return workspace_root, workspace_repo


def parse_score_file(score_path: Path) -> dict:
    if not score_path.exists():
        raise FileNotFoundError(f"STDN score file was not generated: {score_path}")

    lines = [line.strip() for line in score_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("STDN score file is empty.")

    image_name, m_value, s_value, b_value, c_value, t_value = lines[0].split(",")
    return {
        "raw_score": float(m_value),
        "score_source": "M",
        "score_direction_note": (
            "Official STDN test.py was executed on a face-cropped input image. "
            "The app currently interprets the saved M score as a spoof-direction logit after validation "
            "against bundled live/spoof samples."
        ),
        "features": {
            "M": round(float(m_value), 6),
            "s": round(float(s_value), 6),
            "b": round(float(b_value), 6),
            "C": round(float(c_value), 6),
            "T": round(float(t_value), 6),
            "score_file_image": image_name,
        },
    }


def run_inference(repo_dir: Path, checkpoint_dir: Path, input_image: Path) -> dict:
    import_tensorflow()
    checkpoint_prefix = resolve_checkpoint_prefix(checkpoint_dir)
    workspace_root, workspace_repo = prepare_workspace(repo_dir, checkpoint_dir, input_image)
    try:
        import subprocess

        completed = subprocess.run(
            [sys.executable, "test.py"],
            cwd=str(workspace_repo),
            check=False,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "official STDN test.py failed"
            raise RuntimeError(detail)

        score_path = workspace_repo / "log" / "STDN" / "test" / "score.txt"
        payload = parse_score_file(score_path)
        payload["features"]["checkpoint_prefix"] = str(checkpoint_prefix)
        payload["features"]["official_test_script"] = str(workspace_repo / "test.py")
        payload["features"]["official_score_file"] = str(score_path)
        return payload
    finally:
        shutil.rmtree(workspace_root, ignore_errors=True)


def main() -> int:
    args = parse_args()
    repo_dir = Path(args.repo_dir).resolve()
    checkpoint_dir = Path(args.checkpoint_dir).resolve()
    input_image = Path(args.input_image).resolve()
    output_json = Path(args.output_json).resolve()

    if not repo_dir.exists():
        raise FileNotFoundError(f"STDN repository not found: {repo_dir}")
    if not checkpoint_dir.exists():
        raise FileNotFoundError(f"STDN checkpoint directory not found: {checkpoint_dir}")
    if not input_image.exists():
        raise FileNotFoundError(f"Input image not found: {input_image}")

    payload = run_inference(repo_dir=repo_dir, checkpoint_dir=checkpoint_dir, input_image=input_image)
    output_json.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
