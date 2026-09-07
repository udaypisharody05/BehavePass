import math
from collections.abc import Sequence

from .schemas import CanonicalSample


class SampleValidationError(ValueError):
    """A malformed source capture that can be counted and skipped."""


def ensure_unique_sample_ids(samples: Sequence[CanonicalSample]) -> None:
    seen: set[str] = set()
    for sample in samples:
        if sample.sample_id in seen:
            raise SampleValidationError(f"duplicate sample ID: {sample.sample_id}")
        seen.add(sample.sample_id)


def validate_timing_arrays(
    participant_id: str,
    password_id: str,
    keys: Sequence[int],
    press_times: Sequence[float],
    release_times: Sequence[float],
) -> None:
    if not participant_id:
        raise SampleValidationError("missing participant ID")
    if not password_id:
        raise SampleValidationError("missing password ID")
    if not keys:
        raise SampleValidationError("empty key sequence")
    if len(keys) != len(press_times) or len(keys) != len(release_times):
        raise SampleValidationError("key/press/release length mismatch")
    values = [*press_times, *release_times]
    if any(not math.isfinite(value) for value in values):
        raise SampleValidationError("timestamps contain NaN or Inf")
    if any(release < press for press, release in zip(press_times, release_times)):
        raise SampleValidationError("impossible negative dwell time")
    if any(second < first for first, second in zip(press_times, press_times[1:])):
        raise SampleValidationError("press timestamps are not ordered")
