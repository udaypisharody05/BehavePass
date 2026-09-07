from __future__ import annotations

import hashlib
from collections import defaultdict, deque
from pathlib import Path

from .schemas import (
    CanonicalSample,
    DatasetLoadResult,
    DigraphTiming,
    RejectedSample,
    StaticFeatures,
)
from .frontend_static import FrontendStaticFeatureError, extract_frontend_static_features
from .static_features import extract_static_features
from .validation import SampleValidationError, validate_timing_arrays


REQUIRED_FILES = {
    "password.txt",
    "userid.txt",
    "genuine.txt",
    "p_raw_press.txt",
    "p_raw_release.txt",
    "p_pp.txt",
    "p_pr.txt",
    "p_rp.txt",
    "p_rr.txt",
    "p_total.txt",
}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as error:
        raise SampleValidationError(f"cannot read {path.name}: {error}") from error


def _read_raw_timestamps(path: Path) -> tuple[list[int], list[float]]:
    keys: list[int] = []
    timestamps: list[float] = []
    text = _read_text(path)
    if not text:
        raise SampleValidationError(f"{path.name} is empty")
    for line_number, line in enumerate(text.splitlines(), start=1):
        columns = line.split()
        if len(columns) != 2:
            raise SampleValidationError(
                f"{path.name}:{line_number} must contain key code and timestamp"
            )
        try:
            keys.append(int(columns[0]))
            timestamps.append(float(columns[1]))
        except ValueError as error:
            raise SampleValidationError(
                f"{path.name}:{line_number} contains a non-numeric value"
            ) from error
    return keys, timestamps


def _read_vector(path: Path) -> list[float]:
    text = _read_text(path)
    if not text:
        return []
    try:
        return [float(value) for value in text.split()]
    except ValueError as error:
        raise SampleValidationError(f"{path.name} contains a non-numeric value") from error


def _assert_close(name: str, actual: list[float], expected: list[float]) -> None:
    if len(actual) != len(expected):
        raise SampleValidationError(
            f"{name} has {len(actual)} values; expected {len(expected)}"
        )
    if any(abs(left - right) > 1e-6 for left, right in zip(actual, expected)):
        raise SampleValidationError(f"{name} is inconsistent with raw timestamps")


def _password_id(password: str) -> str:
    return "sha256:" + hashlib.sha256(password.encode("utf-8")).hexdigest()


def _align_releases_to_presses(
    press_keys: list[int], release_keys: list[int], release_events: list[float]
) -> list[float]:
    """Pair release events to presses by key code and occurrence order.

    GREYC stores releases in chronological event order, which can differ from
    press order when keys overlap (notably Shift plus another key).
    """
    releases_by_key: dict[int, deque[float]] = defaultdict(deque)
    for key, timestamp in zip(release_keys, release_events):
        releases_by_key[key].append(timestamp)
    aligned: list[float] = []
    for key in press_keys:
        if not releases_by_key[key]:
            raise SampleValidationError(f"no matching release event for key code {key}")
        aligned.append(releases_by_key[key].popleft())
    if any(values for values in releases_by_key.values()):
        raise SampleValidationError("release events remain unmatched")
    return aligned


def parse_greyc_capture(
    capture_dir: Path,
    dataset_root: Path,
    static_features_by_password: dict[str, StaticFeatures] | None = None,
) -> CanonicalSample:
    capture_dir = Path(capture_dir)
    dataset_root = Path(dataset_root)
    missing = sorted(name for name in REQUIRED_FILES if not (capture_dir / name).is_file())
    if missing:
        raise SampleValidationError("missing required files: " + ", ".join(missing))

    press_keys, press_times = _read_raw_timestamps(capture_dir / "p_raw_press.txt")
    release_keys, release_events = _read_raw_timestamps(capture_dir / "p_raw_release.txt")
    if len(press_keys) != len(release_keys):
        raise SampleValidationError("key/press/release length mismatch")
    release_times = _align_releases_to_presses(press_keys, release_keys, release_events)

    password = _read_text(capture_dir / "password.txt")
    if not password:
        raise SampleValidationError("password string is empty")
    typist_raw = _read_text(capture_dir / "userid.txt")
    participant_id = f"user_{int(typist_raw):03d}" if typist_raw.isdigit() else typist_raw
    password_id = _password_id(password)
    validate_timing_arrays(
        participant_id, password_id, press_keys, press_times, release_times
    )

    dwell = [release - press for press, release in zip(press_times, release_times)]
    press_to_press = [next_press - press for press, next_press in zip(press_times, press_times[1:])]
    flight = [next_press - release for release, next_press in zip(release_times, press_times[1:])]
    press_to_next_release = [
        next_release - press for press, next_release in zip(press_times, release_times[1:])
    ]
    release_to_release = [
        next_release - release for release, next_release in zip(release_times, release_times[1:])
    ]
    total = max(release_times) - press_times[0]

    # Supplied p_pr/p_rp arrays use chronological release-event positions, not
    # key-paired releases when overlap changes release order. Validate their
    # actual definitions, while canonical dwell/flight use key-paired releases.
    supplied_pr = [release - press for press, release in zip(press_times, release_events)]
    supplied_rp = [
        next_release - press for press, next_release in zip(press_times, release_events[1:])
    ]
    supplied_rr = [
        next_release - release
        for release, next_release in zip(release_events, release_events[1:])
    ]
    _assert_close("p_pr.txt", _read_vector(capture_dir / "p_pr.txt"), supplied_pr)
    _assert_close("p_pp.txt", _read_vector(capture_dir / "p_pp.txt"), press_to_press)
    _assert_close("p_rp.txt", _read_vector(capture_dir / "p_rp.txt"), supplied_rp)
    _assert_close("p_rr.txt", _read_vector(capture_dir / "p_rr.txt"), supplied_rr)
    supplied_total = _read_vector(capture_dir / "p_total.txt")
    _assert_close("p_total.txt", supplied_total, [total])

    relative = capture_dir.relative_to(dataset_root).as_posix()
    owner_id = next(
        (part for part in capture_dir.parts if part.startswith("user_")), ""
    )
    genuine_text = _read_text(capture_dir / "genuine.txt")
    if genuine_text not in {"0", "1"}:
        raise SampleValidationError("genuine.txt must contain 0 or 1")
    digraphs = tuple(
        DigraphTiming(
            first_key=press_keys[index],
            second_key=press_keys[index + 1],
            press_to_press_ms=press_to_press[index],
            release_to_press_ms=flight[index],
            press_to_release_ms=press_to_next_release[index],
            release_to_release_ms=release_to_release[index],
        )
        for index in range(len(press_keys) - 1)
    )
    static = (
        static_features_by_password.get(password)
        if static_features_by_password is not None
        else None
    ) or extract_static_features(password)
    return CanonicalSample(
        sample_id=f"greyc:{relative}",
        participant_id=participant_id,
        password_id=password_id,
        source="greyc-web-passwords",
        password=password,
        keys=tuple(press_keys),
        press_times_ms=tuple(press_times),
        release_times_ms=tuple(release_times),
        dwell_times_ms=tuple(dwell),
        flight_times_ms=tuple(flight),
        press_to_press_times_ms=tuple(press_to_press),
        digraphs=digraphs,
        total_typing_duration_ms=total,
        static_features=static,
        guess_count=static.guess_count,
        log10_guesses=static.log10_guesses,
        metadata={
            "password_owner_id": owner_id,
            "is_genuine": genuine_text == "1",
            "capture_date": _read_text(capture_dir / "date.txt")
            if (capture_dir / "date.txt").is_file()
            else None,
            "source_path": relative,
            "timing_unit": "milliseconds",
        },
    )


def load_greyc_dataset(
    path: str | Path, *, include_zxcvbn: bool = True
) -> DatasetLoadResult:
    dataset_root = Path(path).expanduser().resolve()
    output_root = dataset_root / "output_numpy"
    passwords_root = output_root / "passwords"
    if not dataset_root.is_dir():
        raise FileNotFoundError(f"GREYC dataset directory does not exist: {dataset_root}")
    if not output_root.is_dir():
        raise FileNotFoundError(f"expected GREYC directory is missing: {output_root}")
    if not passwords_root.is_dir():
        raise FileNotFoundError(f"expected GREYC password corpus is missing: {passwords_root}")

    capture_paths = list(passwords_root.rglob("p_raw_press.txt"))
    static_features_by_password: dict[str, StaticFeatures] = {}
    if include_zxcvbn:
        passwords: set[str] = set()
        for raw_path in capture_paths:
            password_path = raw_path.with_name("password.txt")
            if password_path.is_file():
                try:
                    password = _read_text(password_path)
                    if password:
                        passwords.add(password)
                except SampleValidationError:
                    pass
        try:
            static_features_by_password = extract_frontend_static_features(passwords)
        except FrontendStaticFeatureError:
            # Loading remains usable without Node; availability is explicit in
            # each sample/report rather than replaced with fabricated scores.
            static_features_by_password = {}

    result = DatasetLoadResult()
    seen_ids: set[str] = set()
    for raw_press_path in capture_paths:
        capture_dir = raw_press_path.parent
        relative = capture_dir.relative_to(dataset_root).as_posix()
        try:
            sample = parse_greyc_capture(
                capture_dir, dataset_root, static_features_by_password
            )
            if sample.sample_id in seen_ids:
                raise SampleValidationError(f"duplicate sample ID: {sample.sample_id}")
            seen_ids.add(sample.sample_id)
            result.samples.append(sample)
        except (SampleValidationError, OSError, ValueError) as error:
            result.rejections.append(RejectedSample(relative, str(error)))
    if not result.samples and not result.rejections:
        raise ValueError(f"no GREYC password captures found under {passwords_root}")
    return result
