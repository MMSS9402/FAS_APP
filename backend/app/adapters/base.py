from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from PIL import Image


class BaseFASAdapter(ABC):
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.model_id = config["model_id"]
        self.display_name = config["display_name"]
        self.score_semantics = config["score_semantics"]
        self.threshold = float(config["threshold_default"])

    @abstractmethod
    def load(self) -> None:
        """Load model resources."""

    @abstractmethod
    def predict(self, image: Image.Image) -> Dict[str, Any]:
        """Return raw prediction payload for a single image."""

    def metadata(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "display_name": self.display_name,
            "paper_title": self.config["paper_title"],
            "paper_year": self.config["paper_year"],
            "paper_type": self.config["paper_type"],
            "repository_url": self.config["repository_url"],
            "weights_source": self.config["weights_source"],
            "attack_track": self.config["attack_track"],
            "input_type": self.config["input_type"],
            "ready_status": self.config["ready_status"],
            "implementation_status": self.config.get("implementation_status", "unknown"),
            "score_semantics": self.score_semantics,
            "threshold_default": self.threshold,
            "preprocessing": self.config.get("preprocessing", {}),
        }
