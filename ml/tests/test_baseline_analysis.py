import numpy as np
import pandas as pd

from ml.analysis.analyze_synthetic_dataset import build_model, participant_grouped_split
from ml.analysis.features import (
    FEATURE_GROUPS,
    METADATA_COLUMNS,
    TARGET,
    TARGET_ADJACENT_FEATURES,
    validate_feature_groups,
)


def test_feature_groups_exclude_metadata_and_target() -> None:
    metadata = set(METADATA_COLUMNS)
    for features in FEATURE_GROUPS.values():
        assert TARGET not in features
        assert metadata.isdisjoint(features)
        assert len(features) == len(set(features))


def test_zxcvbn_only_appears_in_explicit_comparison_groups() -> None:
    assert TARGET_ADJACENT_FEATURES == ["zxcvbn_score"]
    assert "zxcvbn_score" not in FEATURE_GROUPS["static_safe"]
    assert "zxcvbn_score" not in FEATURE_GROUPS["combined_safe"]
    assert "zxcvbn_score" in FEATURE_GROUPS["static_with_zxcvbn"]


def test_participant_split_is_reproducible_and_disjoint() -> None:
    data = pd.DataFrame({
        "participant_code": [f"p{group}" for group in range(20) for _ in range(3)],
        "value": range(60),
    })
    first_train, first_test = participant_grouped_split(data, seed=19)
    second_train, second_test = participant_grouped_split(data, seed=19)
    assert np.array_equal(first_train, second_train)
    assert np.array_equal(first_test, second_test)
    assert set(data.iloc[first_train]["participant_code"]).isdisjoint(
        set(data.iloc[first_test]["participant_code"])
    )


def test_scaler_is_fit_on_training_data_only() -> None:
    train_x = pd.DataFrame({"feature": [0.0, 2.0, 4.0]})
    train_y = pd.Series([0.0, 1.0, 2.0])
    test_x = pd.DataFrame({"feature": [1000.0]})
    model = build_model("ridge", seed=42)
    model.fit(train_x, train_y)
    assert model.named_steps["scale"].mean_[0] == 2.0
    assert model.named_steps["scale"].mean_[0] != pd.concat([train_x, test_x])["feature"].mean()
