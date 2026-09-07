from pathlib import Path

import pytest

from ml.data.greyc import load_greyc_dataset, parse_greyc_capture
from ml.data.static_features import extract_static_features
from ml.data.validation import SampleValidationError


def write_capture(
    root: Path,
    *,
    press: str = "65 1000\n66 1080\n",
    release: str = "65 1100\n66 1200\n",
) -> Path:
    capture = root / "output_numpy" / "passwords" / "user_001" / "genuine" / "capture_1"
    capture.mkdir(parents=True)
    files = {
        "password.txt": "Ab1!",
        "userid.txt": "1",
        "genuine.txt": "1",
        "date.txt": "2012-01-01 00:00:00",
        "p_raw_press.txt": press,
        "p_raw_release.txt": release,
        "p_pp.txt": "80",
        "p_pr.txt": "100\n120",
        "p_rp.txt": "200",
        "p_rr.txt": "100",
        "p_total.txt": "200",
    }
    for name, value in files.items():
        (capture / name).write_text(value, encoding="utf-8")
    return capture


def test_parses_canonical_timings_and_negative_flight(tmp_path: Path) -> None:
    capture = write_capture(tmp_path)
    sample = parse_greyc_capture(capture, tmp_path)
    assert sample.participant_id == "user_001"
    assert sample.sequence_length == 2
    assert sample.dwell_times_ms == (100.0, 120.0)
    assert sample.press_to_press_times_ms == (80.0,)
    assert sample.flight_times_ms == (-20.0,)
    assert sample.total_typing_duration_ms == 200.0
    assert sample.digraphs[0].release_to_press_ms == -20.0


def test_loads_dataset_using_pathlib(tmp_path: Path) -> None:
    write_capture(tmp_path)
    result = load_greyc_dataset(Path(tmp_path), include_zxcvbn=False)
    assert len(result.samples) == 1
    assert not result.rejections


def test_pairs_out_of_order_release_events_by_key(tmp_path: Path) -> None:
    capture = write_capture(
        tmp_path,
        press="16 1000\n65 1050\n",
        release="65 1100\n16 1150\n",
    )
    (capture / "p_pr.txt").write_text("100\n100", encoding="utf-8")
    (capture / "p_pp.txt").write_text("50", encoding="utf-8")
    (capture / "p_rp.txt").write_text("150", encoding="utf-8")
    (capture / "p_rr.txt").write_text("50", encoding="utf-8")
    (capture / "p_total.txt").write_text("150", encoding="utf-8")
    sample = parse_greyc_capture(capture, tmp_path)
    assert sample.release_times_ms == (1150.0, 1100.0)
    assert sample.dwell_times_ms == (150.0, 50.0)
    assert sample.flight_times_ms == (-100.0,)


@pytest.mark.parametrize(
    ("press", "release", "reason"),
    [
        ("65 1000\n66 1080\n", "65 1100\n", "length mismatch"),
        ("65 nan\n66 1080\n", "65 1100\n66 1200\n", "NaN or Inf"),
        ("65 1000\n66 inf\n", "65 1100\n66 1200\n", "NaN or Inf"),
        ("65 1000\n66 1080\n", "65 900\n66 1200\n", "negative dwell"),
    ],
)
def test_rejects_malformed_timings(
    tmp_path: Path, press: str, release: str, reason: str
) -> None:
    capture = write_capture(tmp_path, press=press, release=release)
    with pytest.raises(SampleValidationError, match=reason):
        parse_greyc_capture(capture, tmp_path)


def test_loader_counts_malformed_capture(tmp_path: Path) -> None:
    capture = write_capture(tmp_path)
    (capture / "p_total.txt").write_text("999", encoding="utf-8")
    result = load_greyc_dataset(tmp_path, include_zxcvbn=False)
    assert not result.samples
    assert len(result.rejections) == 1
    assert "inconsistent" in result.rejections[0].reason


def test_static_features_match_frontend_field_definitions_and_cache() -> None:
    extract_static_features.cache_clear()
    first = extract_static_features("Ab1!")
    second = extract_static_features("Ab1!")
    assert first is second
    assert first.password_length == 4
    assert (first.lowercase_count, first.uppercase_count) == (1, 1)
    assert (first.digit_count, first.symbol_count) == (1, 1)
    assert first.zxcvbn_score is None
    assert extract_static_features.cache_info().hits == 1
