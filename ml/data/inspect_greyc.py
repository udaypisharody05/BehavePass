from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Iterable

from .greyc import load_greyc_dataset


def _stats(values: Iterable[float]) -> dict[str, float | None]:
    data = list(values)
    if not data:
        return {"min": None, "median": None, "mean": None, "max": None}
    return {
        "min": min(data),
        "median": statistics.median(data),
        "mean": statistics.fmean(data),
        "max": max(data),
    }


def build_report(data_dir: Path) -> dict[str, object]:
    result = load_greyc_dataset(data_dir)
    samples = result.samples
    participants = Counter(sample.participant_id for sample in samples)
    passwords = Counter(sample.password_id for sample in samples)
    return {
        "dataset_path": str(data_dir.resolve()),
        "participants": len(participants),
        "unique_passwords": len(passwords),
        "total_samples": len(samples) + len(result.rejections),
        "valid_samples": len(samples),
        "rejected_samples": len(result.rejections),
        "samples_per_participant": _stats(participants.values()),
        "samples_per_password": _stats(passwords.values()),
        "sequence_length": _stats(sample.sequence_length for sample in samples),
        "dwell_ms": _stats(value for sample in samples for value in sample.dwell_times_ms),
        "flight_ms": _stats(value for sample in samples for value in sample.flight_times_ms),
        "press_to_press_ms": _stats(
            value for sample in samples for value in sample.press_to_press_times_ms
        ),
        "total_typing_duration_ms": _stats(
            sample.total_typing_duration_ms for sample in samples
        ),
        "static_features_available": bool(samples),
        "zxcvbn_available": any(
            sample.static_features.zxcvbn_score is not None for sample in samples
        ),
        "guess_count_available": any(sample.guess_count is not None for sample in samples),
        "log10_guesses_available": any(
            sample.log10_guesses is not None for sample in samples
        ),
        "detected_timing_unit": result.detected_timing_unit,
        "canonical_timing_unit": result.canonical_timing_unit,
        "rejection_reasons": Counter(item.reason for item in result.rejections),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect GREYC-Web without training")
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    report = build_report(args.data_dir)
    rendered = json.dumps(report, indent=2, sort_keys=True, default=dict)
    print(rendered)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
