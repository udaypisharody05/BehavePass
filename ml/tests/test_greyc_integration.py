from pathlib import Path

import pytest

from ml.data.greyc import parse_greyc_capture
from ml.data.frontend_static import extract_frontend_static_features


DATASET = Path(__file__).resolve().parents[2] / "data" / "greyc" / "webkeystroke"


@pytest.mark.integration
def test_real_greyc_first_capture_when_installed() -> None:
    passwords = DATASET / "output_numpy" / "passwords"
    if not passwords.is_dir():
        pytest.skip("local GREYC-Web dataset is not installed")
    raw_path = next(passwords.rglob("p_raw_press.txt"), None)
    if raw_path is None:
        pytest.skip("local GREYC-Web password captures are unavailable")
    sample = parse_greyc_capture(raw_path.parent, DATASET)
    assert sample.source == "greyc-web-passwords"
    assert sample.sequence_length > 0


@pytest.mark.integration
def test_existing_frontend_static_extractor_bridge() -> None:
    features = extract_frontend_static_features({"Synthetic-Only-42!"})["Synthetic-Only-42!"]
    assert features.zxcvbn_score is not None
    assert features.guess_count is not None and features.guess_count >= 1
    assert features.log10_guesses is not None
