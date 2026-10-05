"""Training and evaluation pipeline scaffolding for future fine-tuning experiments.

This module is stubbed for Task 1; no training or dataset creation is executed.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class FineTuningConfig(BaseModel):
    """Configuration schema for future fine-tuning runs."""

    base_model_name: str = "mock-pps-model"
    dataset_path: Optional[str] = None
    output_dir: str = "./checkpoints"
    epochs: int = 3
    learning_rate: float = 2e-5
    batch_size: int = 4
    use_lora: bool = True
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)


class TrainingPipelineStub:
    """Scaffold for training and evaluation pipeline."""

    def __init__(self, config: Optional[FineTuningConfig] = None) -> None:
        self.config = config or FineTuningConfig()

    def run_training_stub(self) -> Dict[str, Any]:
        """Placeholder for training execution."""
        return {
            "status": "ready",
            "message": "Training pipeline scaffold initialized. No training executed in Task 1.",
            "config": self.config.model_dump(),
        }

    def evaluate_stub(self) -> Dict[str, Any]:
        """Placeholder for evaluation metrics calculation."""
        return {
            "status": "ready",
            "message": "Evaluation pipeline scaffold initialized.",
            "metrics": {},
        }
