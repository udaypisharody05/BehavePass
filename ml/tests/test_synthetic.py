import csv
from pathlib import Path
from unittest.mock import patch

import pytest

from ml.data.schemas import StaticFeatures
from ml.data.synthetic import (
    FIELDNAMES,
    PROFILES,
    assert_aggregate_alignment,
    generate_rows,
    generate_rows_and_sequences,
    validate_rows,
    validate_sequence_alignment,
    write_csv,
)


def fake_static(passwords: set[str]) -> dict[str, StaticFeatures]:
    output = {}
    for password in passwords:
        length = len(password)
        lower = sum(char.islower() for char in password)
        upper = sum(char.isupper() for char in password)
        digit = sum(char.isdigit() for char in password)
        symbol = length - lower - upper - digit
        score = min(4, max(0, (length - 5) // 3 + int(symbol > 0)))
        output[password] = StaticFeatures(
            length, lower, upper, digit, symbol, len(set(password)),
            length - len(set(password)), 0, 0, score, 10.0 ** (score + 2),
            float(score + 2), 3.0, 50.0,
        )
    return output


@patch("ml.data.synthetic.extract_frontend_static_features", side_effect=fake_static)
def test_reproducible_for_same_seed(_mock: object) -> None:
    assert generate_rows(40, 42) == generate_rows(40, 42)


@patch("ml.data.synthetic.extract_frontend_static_features", side_effect=fake_static)
def test_schema_count_ranges_labels_and_no_plaintext(_mock: object) -> None:
    rows = generate_rows(120, 7)
    validate_rows(rows, 120)
    assert len(rows) == 120
    assert set(rows[0]) == set(FIELDNAMES)
    assert "password" not in {column.lower() for column in FIELDNAMES}
    assert {int(row["zxcvbn_score"]) for row in rows} <= set(range(5))
    assert all(float(row["total_typing_duration"]) > 0 for row in rows)
    assert all(float(row["average_dwell_time"]) >= 28 for row in rows)


@patch("ml.data.synthetic.extract_frontend_static_features", side_effect=fake_static)
def test_csv_round_trip_has_expected_schema(_mock: object, tmp_path: Path) -> None:
    path = tmp_path / "nested" / "synthetic.csv"
    rows = generate_rows(12, 9)
    write_csv(rows, path)
    with path.open(newline="", encoding="utf-8") as handle:
        loaded = list(csv.DictReader(handle))
    assert len(loaded) == 12
    assert list(loaded[0]) == FIELDNAMES


@patch("ml.data.synthetic.extract_frontend_static_features", side_effect=fake_static)
def test_typing_profiles_have_distinct_timing_distributions(_mock: object) -> None:
    rows = generate_rows(1600, 88)
    means = {}
    variances = {}
    for name in PROFILES:
        subset = [row for row in rows if row["typing_profile"] == name]
        means[name] = sum(float(row["average_press_latency"]) for row in subset) / len(subset)
        variances[name] = sum(float(row["flight_time_std"]) for row in subset) / len(subset)
    assert means["fast"] < means["average"] < means["slow"]
    assert variances["inconsistent"] > variances["average"]


def test_validation_rejects_plaintext_schema() -> None:
    with pytest.raises(ValueError, match="schema"):
        validate_rows([{"password": "forbidden"}], 1)


@patch("ml.data.synthetic.extract_frontend_static_features", side_effect=fake_static)
def test_sequence_and_aggregate_alignment(_mock: object) -> None:
    rows, sequences = generate_rows_and_sequences(80, 42)
    validate_sequence_alignment(rows, sequences)
    existing = [{key: str(value) for key, value in row.items()} for row in rows]
    assert_aggregate_alignment(existing, rows)
    assert all(record["sequence_length"] == len(record["events"]) for record in sequences)
    assert all("key" not in event for record in sequences for event in record["events"])
