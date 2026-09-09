import json
import logging
import math
from pathlib import Path

import pytest
import torch
from fastapi.testclient import TestClient

from app.api import predict as predict_api
from app.main import app
from app.ml.inference import (
    CHECKPOINT_PATH,
    EXPECTED_SEQUENCE_FEATURES,
    EXPECTED_STATIC_FEATURES,
    PREPROCESSING_PATH,
    FusionInference,
    ModelArtifactError,
    get_fusion_inference,
)
from app.schemas.session import KeystrokeFeatureItem, StaticFeaturesSchema


client = TestClient(app)

STATIC_FEATURES = {
    "password_length": 10,
    "lowercase_count": 5,
    "uppercase_count": 2,
    "digit_count": 2,
    "symbol_count": 1,
    "unique_character_count": 8,
    "repeated_character_count": 2,
    "repeated_substring_count": 0,
    "sequential_character_count": 0,
    "zxcvbn_score": 3,
    "log10_estimated_guesses": 6.8,
    "empirical_character_entropy": 3.1,
    "character_pool_entropy_estimate": 55.4,
}

SESSION_FEATURES = {
    "total_typing_duration": 900.0,
    "total_key_presses": 6,
    "average_dwell_time": 82.5,
    "dwell_time_std": 5.0,
    "average_flight_time": 75.0,
    "flight_time_std": 8.0,
    "average_press_latency": 157.5,
    "longest_interkey_delay": 180.0,
    "pause_count": 0,
    "total_pause_duration": 0.0,
    "backspace_count": 0,
    "backspace_rate": 0.0,
    "correction_burst_count": 0,
    "characters_per_second": 6.67,
}


def make_sequence(length: int) -> list[dict[str, object]]:
    return [
        {
            "sequence_index": index,
            "dwell_time": 80.0 + index,
            "flight_time": None if index == 0 else 70.0 + index,
            "press_to_press_latency": None if index == 0 else 150.0 + index,
            "is_backspace": index == length - 1 and length > 3,
            "is_pause": False,
        }
        for index in range(length)
    ]


def make_request(length: int = 6) -> dict[str, object]:
    return {
        "static_features": STATIC_FEATURES,
        "session_features": SESSION_FEATURES,
        "keystroke_sequence": make_sequence(length),
    }


def make_timing_case(
    length: int,
    dwell: float,
    flight: float,
    latency: float,
    *,
    backspace_indices: set[int] | None = None,
    pause_index: int | None = None,
) -> dict[str, object]:
    payload = make_request(length)
    payload["static_features"] = {
        **STATIC_FEATURES,
        "password_length": max(1, length - len(backspace_indices or set())),
    }
    for index, event in enumerate(payload["keystroke_sequence"]):
        event["dwell_time"] = dwell + (index % 3) * 4.0
        event["flight_time"] = None if index == 0 else flight + (index % 2) * 5.0
        event["press_to_press_latency"] = (
            None if index == 0 else latency + (index % 3) * 8.0
        )
        event["is_backspace"] = index in (backspace_indices or set())
        event["is_pause"] = index == pause_index
    if pause_index is not None:
        event = payload["keystroke_sequence"][pause_index]
        event["flight_time"] = 1710.0
        event["press_to_press_latency"] = 1800.0
    return payload


def test_checkpoint_loads_with_expected_architecture_and_metadata():
    inference = FusionInference(CHECKPOINT_PATH, PREPROCESSING_PATH)

    assert not inference.model.training
    assert inference.sequence_mean.shape == (len(EXPECTED_SEQUENCE_FEATURES),)
    assert inference.static_mean.shape == (len(EXPECTED_STATIC_FEATURES),)


def test_inference_is_deterministic_and_cached_once():
    get_fusion_inference.cache_clear()
    first = client.post("/api/predict", json=make_request())
    second = client.post("/api/predict", json=make_request())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["fusion_log10_estimated_guesses"] == second.json()[
        "fusion_log10_estimated_guesses"
    ]
    assert math.isfinite(first.json()["fusion_log10_estimated_guesses"])
    assert first.json()["model_type"] == "BiLSTM + MLP fusion"
    assert first.json()["target"] == "log10 estimated guesses"
    assert get_fusion_inference.cache_info().misses == 1
    assert get_fusion_inference.cache_info().hits == 1


def test_preprocessing_uses_saved_values_and_exact_feature_order():
    inference = FusionInference(CHECKPOINT_PATH, PREPROCESSING_PATH)
    metadata = json.loads(PREPROCESSING_PATH.read_text(encoding="utf-8"))
    items = [KeystrokeFeatureItem(**item) for item in make_sequence(2)]
    actual_sequence = inference.preprocess_sequence(items)
    raw_sequence = torch.tensor(
        [
            [80.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [81.0, 71.0, 151.0, 1.0, 0.0, 0.0],
        ],
        dtype=torch.float32,
    )
    expected_sequence = (
        raw_sequence - torch.tensor(metadata["sequence_mean"])
    ) / torch.tensor(metadata["sequence_std"])
    assert torch.allclose(actual_sequence, expected_sequence)

    static = StaticFeaturesSchema(**STATIC_FEATURES)
    raw_static = torch.tensor(
        [float(STATIC_FEATURES[name]) for name in EXPECTED_STATIC_FEATURES]
    )
    expected_static = (
        raw_static - torch.tensor(metadata["static_mean"])
    ) / torch.tensor(metadata["static_std"])
    assert torch.allclose(inference.preprocess_static(static), expected_static)
    assert not hasattr(inference, "fit")


@pytest.mark.parametrize("length", [1, 3, 12, 40])
def test_variable_length_sequences(length: int):
    response = client.post("/api/predict", json=make_request(length))

    assert response.status_code == 200
    assert math.isfinite(response.json()["fusion_log10_estimated_guesses"])
    if length < 6 or length > 27:
        assert response.json()["warnings"]


def test_malformed_sequence_is_rejected():
    payload = make_request()
    payload["keystroke_sequence"][2]["sequence_index"] = 8

    response = client.post("/api/predict", json=payload)

    assert response.status_code == 422
    assert "contiguous" in response.json()["detail"]


def test_missing_checkpoint_preserves_static_response(monkeypatch, tmp_path: Path):
    def missing_artifact():
        return FusionInference(tmp_path / "missing.pt", PREPROCESSING_PATH)

    monkeypatch.setattr(predict_api, "get_fusion_inference", missing_artifact)
    response = client.post("/api/predict", json=make_request())

    assert response.status_code == 200
    assert response.json()["behavioural_model_status"] == "model_unavailable"
    assert response.json()["fusion_log10_estimated_guesses"] is None
    assert "checkpoint is missing" in response.json()["warnings"][0]
    assert str(tmp_path / "missing.pt") in response.json()["warnings"][0]


def test_invalid_checkpoint_is_reported_as_artifact_error(tmp_path: Path):
    invalid_checkpoint = tmp_path / "invalid.pt"
    invalid_checkpoint.write_bytes(b"not a PyTorch checkpoint")

    with pytest.raises(ModelArtifactError, match="could not be loaded"):
        FusionInference(invalid_checkpoint, PREPROCESSING_PATH)


def test_invalid_preprocessing_is_reported_as_artifact_error(tmp_path: Path):
    invalid_metadata = tmp_path / "invalid.json"
    invalid_metadata.write_text("not json", encoding="utf-8")

    with pytest.raises(ModelArtifactError, match="could not be loaded"):
        FusionInference(CHECKPOINT_PATH, invalid_metadata)


def test_model_failure_returns_concise_error_without_traceback(monkeypatch):
    class FailingInference:
        def predict(self, sequence, static_features):
            from app.ml.inference import ModelInferenceError

            raise ModelInferenceError("internal tensor detail")

    monkeypatch.setattr(predict_api, "get_fusion_inference", lambda: FailingInference())
    response = client.post("/api/predict", json=make_request())

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Fusion model inference failed; verify the backend logs and demo artifacts."
    )
    assert "tensor" not in response.text


def test_plaintext_field_is_rejected_and_not_logged(caplog):
    marker = "DEMO-PLAINTEXT-MUST-NOT-PERSIST-7f99"
    payload = make_request()
    payload["password"] = marker

    with caplog.at_level(logging.DEBUG):
        response = client.post("/api/predict", json=payload)

    assert response.status_code == 422
    assert marker not in caplog.text


@pytest.mark.parametrize(
    ("case_name", "payload"),
    [
        ("fast", make_timing_case(10, 35.0, 25.0, 60.0)),
        ("average", make_timing_case(12, 90.0, 100.0, 190.0)),
        ("slow", make_timing_case(10, 180.0, 350.0, 530.0)),
        (
            "several_backspaces",
            make_timing_case(14, 95.0, 110.0, 205.0, backspace_indices={6, 7, 11}),
        ),
        ("one_long_pause", make_timing_case(11, 85.0, 90.0, 175.0, pause_index=5)),
        ("short_password", make_timing_case(3, 75.0, 70.0, 145.0)),
        ("longer_password", make_timing_case(24, 88.0, 92.0, 180.0)),
    ],
)
def test_realistic_derived_only_browser_ranges(case_name: str, payload: dict[str, object]):
    response = client.post("/api/predict", json=payload)

    assert response.status_code == 200, case_name
    prediction = response.json()["fusion_log10_estimated_guesses"]
    assert math.isfinite(prediction), case_name
    # Broad demo-sanity bound, not an evaluation or output adjustment.
    assert 0.0 <= prediction <= 30.0, (case_name, prediction)
