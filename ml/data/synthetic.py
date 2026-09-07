"""Reproducible synthetic BehavePass sessions for pipeline development only."""

from __future__ import annotations

import csv
import json
import math
import random
import statistics
import string
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .frontend_static import extract_frontend_static_features


PAUSE_THRESHOLD_MS = 500.0
SOURCE = "synthetic_behavepass_v1"


@dataclass(frozen=True)
class TypingProfile:
    dwell_mean: float
    dwell_cv: float
    flight_mean: float
    flight_sd: float
    pause_probability: float
    backspace_probability: float


PROFILES = {
    "fast": TypingProfile(68, 0.20, 55, 28, 0.018, 0.025),
    "average": TypingProfile(92, 0.25, 105, 48, 0.035, 0.045),
    "slow": TypingProfile(130, 0.28, 185, 70, 0.060, 0.070),
    "inconsistent": TypingProfile(105, 0.55, 125, 125, 0.095, 0.085),
}


FIELDNAMES = [
    "session_id", "source", "synthetic_seed", "participant_code",
    "typing_profile", "task_type", "pause_threshold_ms",
    "password_length", "lowercase_count", "uppercase_count", "digit_count",
    "symbol_count", "unique_character_count", "repeated_character_count",
    "repeated_substring_count", "sequential_character_count", "zxcvbn_score",
    "log10_estimated_guesses", "empirical_character_entropy",
    "character_pool_entropy_estimate", "total_typing_duration",
    "total_key_presses", "average_dwell_time", "dwell_time_std",
    "average_flight_time", "flight_time_std", "average_press_latency",
    "longest_interkey_delay", "pause_count", "total_pause_duration",
    "backspace_count", "backspace_rate", "correction_burst_count",
    "characters_per_second",
]

METADATA_FIELDS = {
    "session_id", "source", "synthetic_seed", "participant_code",
    "typing_profile", "task_type", "pause_threshold_ms",
}


def _clip(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def _password(rng: random.Random) -> str:
    complexity = rng.choices((0, 1, 2, 3, 4), weights=(10, 18, 28, 27, 17))[0]
    length_ranges = ((6, 9), (7, 11), (9, 13), (11, 16), (14, 20))
    length = rng.randint(*length_ranges[complexity])
    common = ["password", "welcome", "dragon", "monkey", "qwerty", "letmein"]
    if complexity <= 1 and rng.random() < 0.48:
        base = rng.choice(common)
        suffix = str(rng.randint(0, 999)) if complexity else ""
        return (base + suffix)[:length].ljust(length, base[-1])
    pools = [string.ascii_lowercase]
    if complexity >= 1:
        pools.append(string.digits)
    if complexity >= 2:
        pools.append(string.ascii_uppercase)
    if complexity >= 3:
        pools.append("!@#$%^&*-_=+")
    required = [rng.choice(pool) for pool in pools]
    combined = "".join(pools)
    chars = required + [rng.choice(combined) for _ in range(length - len(required))]
    rng.shuffle(chars)
    return "".join(chars)


def _mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def _pstdev(values: list[float]) -> float:
    return statistics.pstdev(values) if len(values) > 1 else 0.0


def _session_features(
    rng: random.Random, password_length: int, zxcvbn_score: int, profile: TypingProfile
) -> dict[str, float | int]:
    aggregates, _ = _simulate_session(
        rng, password_length, zxcvbn_score, profile, sequence_seed=0
    )
    return aggregates


def _backspace_flags(total_keys: int, backspaces: int, bursts: int, seed: int) -> list[bool]:
    flags = [False] * total_keys
    cursor = 1 if total_keys > 2 else 0
    for _ in range(bursts):
        while cursor + 1 < total_keys and (flags[cursor] or flags[cursor + 1]):
            cursor += 1
        if cursor + 1 >= total_keys:
            break
        flags[cursor] = flags[cursor + 1] = True
        cursor += 3
    remaining = backspaces - sum(flags)
    candidates = [index for index in range(total_keys) if not flags[index]]
    random.Random(seed).shuffle(candidates)
    for index in candidates[:remaining]:
        flags[index] = True
    return flags


def _simulate_session(
    rng: random.Random,
    password_length: int,
    zxcvbn_score: int,
    profile: TypingProfile,
    sequence_seed: int,
) -> tuple[dict[str, float | int], list[dict[str, object]]]:
    difficulty = 1.0 + 0.018 * max(password_length - 10, 0) + 0.025 * zxcvbn_score
    correction_probability = min(
        0.20,
        profile.backspace_probability * difficulty
        + 0.004 * max(password_length - 8, 0),
    )
    backspaces = sum(rng.random() < correction_probability for _ in range(password_length))
    if rng.random() < correction_probability * 0.35:
        backspaces += rng.randint(1, 2)
    total_keys = password_length + backspaces
    pause_probability = min(
        0.25,
        profile.pause_probability * difficulty
        + 0.0025 * max(password_length - 10, 0)
        + 0.008 * backspaces,
    )

    sigma = math.sqrt(math.log1p(profile.dwell_cv**2))
    mu = math.log(profile.dwell_mean) - sigma * sigma / 2
    dwell = [_clip(rng.lognormvariate(mu, sigma), 28, 380) for _ in range(total_keys)]
    flight: list[float] = []
    press_latency: list[float] = []
    pauses: list[float] = []
    for index in range(1, total_keys):
        current_flight = _clip(rng.gauss(profile.flight_mean, profile.flight_sd), -90, 430)
        latency = max(12.0, dwell[index - 1] + current_flight)
        if rng.random() < pause_probability:
            latency += _clip(rng.lognormvariate(math.log(650), 0.48), 350, 2800)
        current_flight = latency - dwell[index - 1]
        flight.append(current_flight)
        press_latency.append(latency)
        if latency >= PAUSE_THRESHOLD_MS:
            pauses.append(latency)

    press_times = [0.0]
    for latency in press_latency:
        press_times.append(press_times[-1] + latency)
    total_duration = max(
        press + duration for press, duration in zip(press_times, dwell)
    )
    correction_bursts = 0
    remaining = backspaces
    while remaining >= 2:
        if rng.random() < 0.45:
            correction_bursts += 1
            remaining -= 2
        else:
            remaining -= 1
    aggregates: dict[str, float | int] = {
        "total_typing_duration": total_duration,
        "total_key_presses": total_keys,
        "average_dwell_time": _mean(dwell),
        "dwell_time_std": _pstdev(dwell),
        "average_flight_time": _mean(flight),
        "flight_time_std": _pstdev(flight),
        "average_press_latency": _mean(press_latency),
        "longest_interkey_delay": max(press_latency, default=0.0),
        "pause_count": len(pauses),
        "total_pause_duration": sum(pauses),
        "backspace_count": backspaces,
        "backspace_rate": backspaces / total_keys,
        "correction_burst_count": correction_bursts,
        "characters_per_second": password_length / (total_duration / 1000),
    }
    backspace_flags = _backspace_flags(
        total_keys, backspaces, correction_bursts, sequence_seed
    )
    sequence = []
    for index in range(total_keys):
        latency = press_latency[index - 1] if index else None
        current_flight = flight[index - 1] if index else None
        sequence.append({
            "sequence_index": index,
            "normalized_position": index / max(1, total_keys - 1),
            "press_time_ms": press_times[index],
            "release_time_ms": press_times[index] + dwell[index],
            "dwell_time": dwell[index],
            "flight_time": current_flight,
            "press_to_press_latency": latency,
            "release_to_press_latency": current_flight,
            "is_pause": bool(latency is not None and latency >= PAUSE_THRESHOLD_MS),
            "is_backspace": backspace_flags[index],
        })
    return aggregates, sequence


def generate_rows(samples: int, seed: int) -> list[dict[str, object]]:
    rows, _ = generate_rows_and_sequences(samples, seed)
    return rows


def generate_rows_and_sequences(
    samples: int, seed: int
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    if samples <= 0:
        raise ValueError("samples must be positive")
    rng = random.Random(seed)
    plans = []
    for index in range(samples):
        plans.append((index, rng.choice(tuple(PROFILES)), _password(rng)))
    static_by_password = extract_frontend_static_features({item[2] for item in plans})

    rows: list[dict[str, object]] = []
    sequences: list[dict[str, object]] = []
    for index, profile_name, password in plans:
        static = static_by_password[password]
        timing, events = _simulate_session(
            rng,
            static.password_length,
            int(static.zxcvbn_score),
            PROFILES[profile_name],
            sequence_seed=(seed * 1_000_003 + index),
        )
        row: dict[str, object] = {
            "session_id": f"SYN-{seed}-{index:06d}",
            "source": SOURCE,
            "synthetic_seed": seed,
            "participant_code": f"SYN-P{rng.randint(1, 240):03d}",
            "typing_profile": profile_name,
            "task_type": "synthetic_creation",
            "pause_threshold_ms": PAUSE_THRESHOLD_MS,
            "password_length": static.password_length,
            "lowercase_count": static.lowercase_count,
            "uppercase_count": static.uppercase_count,
            "digit_count": static.digit_count,
            "symbol_count": static.symbol_count,
            "unique_character_count": static.unique_character_count,
            "repeated_character_count": static.repeated_character_count,
            "repeated_substring_count": static.repeated_substring_count,
            "sequential_character_count": static.sequential_character_count,
            "zxcvbn_score": static.zxcvbn_score,
            "log10_estimated_guesses": static.log10_guesses,
            "empirical_character_entropy": static.empirical_character_entropy,
            "character_pool_entropy_estimate": static.character_pool_entropy_estimate,
            **timing,
        }
        for key, value in tuple(row.items()):
            if isinstance(value, float):
                row[key] = round(value, 4)
        rows.append(row)
        sequences.append({
            "session_id": row["session_id"],
            "participant_code": row["participant_code"],
            "source": "synthetic_behavepass_sequence_v1",
            "sequence_length": len(events),
            "events": [
                {
                    key: round(value, 4) if isinstance(value, float) else value
                    for key, value in event.items()
                }
                for event in events
            ],
        })
    return rows, sequences


def write_sequences_jsonl(sequences: Iterable[dict[str, object]], output: Path) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for sequence in sequences:
            handle.write(json.dumps(sequence, separators=(",", ":")) + "\n")


def read_sequences_jsonl(path: Path) -> list[dict[str, object]]:
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def assert_aggregate_alignment(
    existing_rows: list[dict[str, str]], regenerated_rows: list[dict[str, object]]
) -> None:
    if len(existing_rows) != len(regenerated_rows):
        raise ValueError("existing and regenerated aggregate row counts differ")
    numeric_fields = set(FIELDNAMES) - {
        "session_id", "source", "participant_code", "typing_profile", "task_type"
    }
    for row_number, (existing, regenerated) in enumerate(
        zip(existing_rows, regenerated_rows), start=2
    ):
        for field in FIELDNAMES:
            if field in numeric_fields:
                if abs(float(existing[field]) - float(regenerated[field])) > 5e-5:
                    raise ValueError(
                        f"aggregate mismatch at CSV row {row_number}, field {field}"
                    )
            elif existing[field] != str(regenerated[field]):
                raise ValueError(
                    f"aggregate mismatch at CSV row {row_number}, field {field}"
                )


def validate_sequence_alignment(
    aggregate_rows: list[dict[str, object]], sequences: list[dict[str, object]]
) -> None:
    if len(aggregate_rows) != len(sequences):
        raise ValueError("aggregate and sequence counts differ")
    for row, record in zip(aggregate_rows, sequences):
        if row["session_id"] != record["session_id"]:
            raise ValueError("sequence session_id does not match aggregate row")
        events = record["events"]
        if not isinstance(events, list) or not events:
            raise ValueError("sequence is empty")
        dwell = [float(event["dwell_time"]) for event in events]
        flight = [float(event["flight_time"]) for event in events[1:]]
        latencies = [float(event["press_to_press_latency"]) for event in events[1:]]
        tolerance = 1e-3
        checks = {
            "total_key_presses": len(events),
            "average_dwell_time": _mean(dwell),
            "dwell_time_std": _pstdev(dwell),
            "average_flight_time": _mean(flight),
            "flight_time_std": _pstdev(flight),
            "average_press_latency": _mean(latencies),
            "longest_interkey_delay": max(latencies, default=0.0),
            "pause_count": sum(bool(event["is_pause"]) for event in events),
            "total_pause_duration": sum(
                float(event["press_to_press_latency"])
                for event in events if event["is_pause"]
            ),
            "backspace_count": sum(bool(event["is_backspace"]) for event in events),
            "total_typing_duration": max(float(event["release_time_ms"]) for event in events),
        }
        for field, derived in checks.items():
            if abs(float(row[field]) - float(derived)) > tolerance:
                raise ValueError(f"sequence aggregate mismatch for {row['session_id']}: {field}")


def write_csv(rows: Iterable[dict[str, object]], output: Path) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_rows(rows: list[dict[str, object]], expected_count: int | None = None) -> None:
    if expected_count is not None and len(rows) != expected_count:
        raise ValueError(f"expected {expected_count} rows; found {len(rows)}")
    if not rows:
        raise ValueError("dataset is empty")
    columns = set(rows[0])
    if columns != set(FIELDNAMES):
        raise ValueError("dataset schema does not match the expected synthetic schema")
    if any("password" == column.lower() or "plaintext" in column.lower() for column in columns):
        raise ValueError("plaintext password column is forbidden")
    if any(value in (None, "") for row in rows for value in row.values()):
        raise ValueError("dataset contains unexpected null/empty values")
    numeric = lambda row, key: float(row[key])
    for row in rows:
        if row["source"] != SOURCE or row["typing_profile"] not in PROFILES:
            raise ValueError("invalid synthetic provenance or typing profile")
        if int(float(row["zxcvbn_score"])) not in range(5):
            raise ValueError("zxcvbn_score must be between 0 and 4")
        if not 28 <= numeric(row, "average_dwell_time") <= 380:
            raise ValueError("average dwell time is outside realistic bounds")
        if not -90 <= numeric(row, "average_flight_time") <= 2800:
            raise ValueError("average flight time is outside realistic bounds")
        for key in (
            "total_typing_duration", "dwell_time_std", "flight_time_std",
            "average_press_latency", "longest_interkey_delay", "total_pause_duration",
            "backspace_rate", "characters_per_second", "log10_estimated_guesses",
        ):
            if not math.isfinite(numeric(row, key)) or numeric(row, key) < 0:
                raise ValueError(f"{key} must be finite and non-negative")
    for key in ("average_dwell_time", "average_flight_time", "total_typing_duration"):
        if len({row[key] for row in rows}) < min(5, len(rows)):
            raise ValueError(f"{key} lacks meaningful variance")
    distribution = Counter(int(float(row["zxcvbn_score"])) for row in rows)
    if len(rows) >= 100 and max(distribution.values()) / len(rows) > 0.75:
        raise ValueError("target distribution is excessively imbalanced")


def summary(rows: list[dict[str, object]]) -> dict[str, object]:
    values = lambda key: [float(row[key]) for row in rows]
    return {
        "sample_count": len(rows),
        "feature_count": len(FIELDNAMES) - len(METADATA_FIELDS),
        "zxcvbn_score_distribution": dict(sorted(Counter(int(float(row["zxcvbn_score"])) for row in rows).items())),
        "mean_dwell_ms": round(statistics.fmean(values("average_dwell_time")), 2),
        "median_dwell_ms": round(statistics.median(values("average_dwell_time")), 2),
        "mean_flight_ms": round(statistics.fmean(values("average_flight_time")), 2),
        "median_flight_ms": round(statistics.median(values("average_flight_time")), 2),
        "average_backspace_count": round(statistics.fmean(values("backspace_count")), 2),
        "average_pause_count": round(statistics.fmean(values("pause_count")), 2),
        "typing_profile_distribution": dict(
            sorted(Counter(str(row["typing_profile"]) for row in rows).items())
        ),
    }
