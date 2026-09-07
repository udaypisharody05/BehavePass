from __future__ import annotations

import json
import math
import sys
from functools import lru_cache
from pathlib import Path

import torch

from app.schemas.session import KeystrokeFeatureItem, StaticFeaturesSchema


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CHECKPOINT_PATH = PROJECT_ROOT / "ml" / "checkpoints" / "fusion_bilstm.pt"
PREPROCESSING_PATH = PROJECT_ROOT / "ml" / "results" / "sequence_preprocessing.json"

EXPECTED_SEQUENCE_FEATURES = [
    "dwell_time",
    "flight_time",
    "press_to_press_latency",
    "normalized_position",
    "is_pause",
    "is_backspace",
]
EXPECTED_STATIC_FEATURES = [
    "password_length",
    "lowercase_count",
    "uppercase_count",
    "digit_count",
    "symbol_count",
    "unique_character_count",
    "repeated_character_count",
    "repeated_substring_count",
    "sequential_character_count",
    "empirical_character_entropy",
    "character_pool_entropy_estimate",
]


class ModelArtifactError(RuntimeError):
    pass


class InferenceInputError(ValueError):
    pass


class ModelInferenceError(RuntimeError):
    pass


def validate_demo_artifact_paths(
    checkpoint_path: Path = CHECKPOINT_PATH,
    preprocessing_path: Path = PREPROCESSING_PATH,
) -> None:
    if not checkpoint_path.is_file():
        raise ModelArtifactError(
            "BehavePass demo checkpoint is missing. Place fusion_bilstm.pt at: "
            f"{checkpoint_path}"
        )
    if not preprocessing_path.is_file():
        raise ModelArtifactError(
            "BehavePass preprocessing metadata is missing. Place "
            f"sequence_preprocessing.json at: {preprocessing_path}"
        )


class FusionInference:
    def __init__(self, checkpoint_path: Path, preprocessing_path: Path) -> None:
        validate_demo_artifact_paths(checkpoint_path, preprocessing_path)
        metadata = json.loads(preprocessing_path.read_text(encoding="utf-8"))
        if metadata.get("sequence_features") != EXPECTED_SEQUENCE_FEATURES:
            raise ModelArtifactError("checkpoint sequence feature order is incompatible")
        if metadata.get("static_features") != EXPECTED_STATIC_FEATURES:
            raise ModelArtifactError("checkpoint static feature order is incompatible")
        expected_metadata_lengths = {
            "sequence_mean": len(EXPECTED_SEQUENCE_FEATURES),
            "sequence_std": len(EXPECTED_SEQUENCE_FEATURES),
            "static_mean": len(EXPECTED_STATIC_FEATURES),
            "static_std": len(EXPECTED_STATIC_FEATURES),
        }
        for name, expected_length in expected_metadata_lengths.items():
            if len(metadata.get(name, [])) != expected_length:
                raise ModelArtifactError(
                    f"preprocessing metadata field {name} has an incompatible dimension"
                )
        if any(value <= 0 for value in metadata["sequence_std"] + metadata["static_std"]):
            raise ModelArtifactError("preprocessing metadata contains a non-positive standard deviation")
        if "target_mean" not in metadata or float(metadata.get("target_std", 0)) <= 0:
            raise ModelArtifactError("target preprocessing metadata is incomplete or invalid")

        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
        from ml.sequence.models import build_neural_model

        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
        if checkpoint.get("model_name") != "fusion_bilstm":
            raise ModelArtifactError("checkpoint is not the fusion BiLSTM model")
        if checkpoint.get("sequence_size") != len(EXPECTED_SEQUENCE_FEATURES):
            raise ModelArtifactError("checkpoint sequence dimension is incompatible")
        if checkpoint.get("static_size") != len(EXPECTED_STATIC_FEATURES):
            raise ModelArtifactError("checkpoint static dimension is incompatible")
        if checkpoint.get("seed") != metadata.get("seed"):
            raise ModelArtifactError("checkpoint and preprocessing metadata seeds do not match")
        self.model = build_neural_model(
            checkpoint["model_name"],
            checkpoint["sequence_size"],
            checkpoint["static_size"],
            checkpoint["hidden_size"],
        )
        try:
            self.model.load_state_dict(checkpoint["state_dict"])
        except (KeyError, RuntimeError) as error:
            raise ModelArtifactError("fusion checkpoint weights are incompatible") from error
        self.model.eval()
        self.sequence_mean = torch.tensor(metadata["sequence_mean"], dtype=torch.float32)
        self.sequence_std = torch.tensor(metadata["sequence_std"], dtype=torch.float32)
        self.static_mean = torch.tensor(metadata["static_mean"], dtype=torch.float32)
        self.static_std = torch.tensor(metadata["static_std"], dtype=torch.float32)
        self.target_mean = float(metadata["target_mean"])
        self.target_std = float(metadata["target_std"])

    def preprocess_sequence(self, items: list[KeystrokeFeatureItem]) -> torch.Tensor:
        if not items:
            raise InferenceInputError("keystroke sequence is empty")
        if len(items) > 512:
            raise InferenceInputError("keystroke sequence exceeds the 512-event safety limit")
        ordered = sorted(items, key=lambda item: item.sequence_index)
        if [item.sequence_index for item in ordered] != list(range(len(ordered))):
            raise InferenceInputError("sequence_index values must be contiguous from zero")
        denominator = max(1, len(ordered) - 1)
        rows = []
        for index, item in enumerate(ordered):
            flight = 0.0 if item.flight_time is None else item.flight_time
            latency = 0.0 if item.press_to_press_latency is None else item.press_to_press_latency
            values = [
                item.dwell_time,
                flight,
                latency,
                index / denominator,
                float(item.is_pause),
                float(item.is_backspace),
            ]
            if any(not math.isfinite(value) for value in values):
                raise InferenceInputError("sequence contains NaN or infinite values")
            if item.dwell_time < 0 or latency < 0:
                raise InferenceInputError("dwell and press-to-press latency must be non-negative")
            if index > 0 and (
                item.flight_time is None or item.press_to_press_latency is None
            ):
                raise InferenceInputError("only the first event may omit flight/latency")
            rows.append(values)
        sequence = torch.tensor(rows, dtype=torch.float32)
        return (sequence - self.sequence_mean) / self.sequence_std

    def preprocess_static(self, features: StaticFeaturesSchema) -> torch.Tensor:
        values = torch.tensor(
            [float(getattr(features, name)) for name in EXPECTED_STATIC_FEATURES],
            dtype=torch.float32,
        )
        if not torch.isfinite(values).all():
            raise InferenceInputError("static features contain NaN or infinite values")
        return (values - self.static_mean) / self.static_std

    def predict(
        self,
        sequence: list[KeystrokeFeatureItem],
        static_features: StaticFeaturesSchema,
    ) -> float:
        sequence_tensor = self.preprocess_sequence(sequence).unsqueeze(0)
        static_tensor = self.preprocess_static(static_features).unsqueeze(0)
        lengths = torch.tensor([len(sequence)], dtype=torch.long)
        try:
            with torch.no_grad():
                normalized = self.model(sequence_tensor, lengths, static_tensor)
            prediction = float(normalized.item() * self.target_std + self.target_mean)
        except RuntimeError as error:
            raise ModelInferenceError("fusion model inference failed") from error
        if not math.isfinite(prediction):
            raise ModelInferenceError("fusion model returned a non-finite prediction")
        return prediction


@lru_cache(maxsize=1)
def get_fusion_inference() -> FusionInference:
    """Load and cache model artifacts once per backend process."""
    return FusionInference(CHECKPOINT_PATH, PREPROCESSING_PATH)
