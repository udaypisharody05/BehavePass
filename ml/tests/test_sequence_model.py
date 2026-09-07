from pathlib import Path

import pandas as pd
import torch

from ml.analysis.features import METADATA_COLUMNS, STATIC_FEATURES, TARGET
from ml.sequence.models import build_neural_model
from ml.sequence.preprocessing import SEQUENCE_FEATURES, collate_sequences, split_participants


def test_variable_length_padding_and_mask() -> None:
    first = (torch.ones(2, 6), torch.ones(11), torch.tensor(1.0), "a")
    second = (torch.ones(4, 6), torch.ones(11), torch.tensor(2.0), "b")
    padded, lengths, mask, static, target, ids = collate_sequences([first, second])
    assert padded.shape == (2, 4, 6)
    assert lengths.tolist() == [2, 4]
    assert mask.tolist() == [[True, True, False, False], [True, True, True, True]]
    assert static.shape == (2, 11) and target.shape == (2,) and ids == ["a", "b"]


def test_sequence_inputs_exclude_metadata_and_target() -> None:
    assert TARGET not in SEQUENCE_FEATURES
    assert set(SEQUENCE_FEATURES).isdisjoint(METADATA_COLUMNS)
    assert "zxcvbn_score" not in STATIC_FEATURES


def test_model_forward_dimensions_and_reproducibility() -> None:
    sequence = torch.randn(3, 7, 6)
    lengths = torch.tensor([7, 5, 3])
    static = torch.randn(3, 11)
    for name in ("behavior_bilstm", "static_mlp", "fusion_bilstm"):
        torch.manual_seed(42)
        first = build_neural_model(name)
        torch.manual_seed(42)
        second = build_neural_model(name)
        assert first(sequence, lengths, static).shape == (3,)
        assert torch.equal(first(sequence, lengths, static), second(sequence, lengths, static))


def test_train_validation_test_participants_are_disjoint_and_reproducible() -> None:
    rows = []
    for participant in range(40):
        for session in range(3):
            rows.append({"participant_code": f"p{participant}", "session_id": f"s{participant}-{session}"})
    data = pd.DataFrame(rows)
    first = split_participants(data, seed=42)
    second = split_participants(data, seed=42)
    for left, right in zip(first, second):
        assert left["session_id"].tolist() == right["session_id"].tolist()
    groups = [set(frame["participant_code"]) for frame in first]
    assert groups[0].isdisjoint(groups[1])
    assert groups[0].isdisjoint(groups[2])
    assert groups[1].isdisjoint(groups[2])


def test_checkpoint_round_trip(tmp_path: Path) -> None:
    torch.manual_seed(8)
    original = build_neural_model("fusion_bilstm")
    path = tmp_path / "model.pt"
    torch.save({"model_name": "fusion_bilstm", "state_dict": original.state_dict()}, path)
    checkpoint = torch.load(path, weights_only=True)
    restored = build_neural_model(checkpoint["model_name"])
    restored.load_state_dict(checkpoint["state_dict"])
    for expected, actual in zip(original.parameters(), restored.parameters()):
        assert torch.equal(expected, actual)
