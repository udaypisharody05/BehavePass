from dataclasses import replace

import pytest

from ml.data.schemas import CanonicalSample, StaticFeatures
from ml.data.split import grouped_password_split
from ml.data.validation import SampleValidationError, ensure_unique_sample_ids


STATIC = StaticFeatures(1, 1, 0, 0, 0, 1, 0, 0, 0)


def sample(sample_id: str, password_id: str) -> CanonicalSample:
    return CanonicalSample(
        sample_id=sample_id,
        participant_id="user_001",
        password_id=password_id,
        source="test",
        password="x",
        keys=(88,),
        press_times_ms=(0.0,),
        release_times_ms=(10.0,),
        dwell_times_ms=(10.0,),
        flight_times_ms=(),
        press_to_press_times_ms=(),
        digraphs=(),
        total_typing_duration_ms=10.0,
        static_features=STATIC,
        guess_count=None,
        log10_guesses=None,
    )


def test_password_grouped_split_prevents_leakage_and_is_deterministic() -> None:
    samples = [sample(f"s-{password}-{trial}", password) for password in "abcdefghij" for trial in range(2)]
    first = grouped_password_split(samples, seed=7)
    second = grouped_password_split(samples, seed=7)
    assert [[item.sample_id for item in first[name]] for name in first] == [
        [item.sample_id for item in second[name]] for name in second
    ]
    ids = {name: {item.password_id for item in values} for name, values in first.items()}
    assert ids["train"].isdisjoint(ids["validation"])
    assert ids["train"].isdisjoint(ids["test"])
    assert ids["validation"].isdisjoint(ids["test"])


def test_duplicate_sample_ids_are_rejected() -> None:
    original = sample("duplicate", "a")
    duplicate = replace(original, password_id="b")
    with pytest.raises(SampleValidationError, match="duplicate sample ID"):
        ensure_unique_sample_ids([original, duplicate])
