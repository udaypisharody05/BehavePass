from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StaticFeatures:
    password_length: int
    lowercase_count: int
    uppercase_count: int
    digit_count: int
    symbol_count: int
    unique_character_count: int
    repeated_character_count: int
    repeated_substring_count: int
    sequential_character_count: int
    zxcvbn_score: int | None = None
    guess_count: float | None = None
    log10_guesses: float | None = None
    empirical_character_entropy: float | None = None
    character_pool_entropy_estimate: float | None = None


@dataclass(frozen=True)
class DigraphTiming:
    first_key: int
    second_key: int
    press_to_press_ms: float
    release_to_press_ms: float
    press_to_release_ms: float
    release_to_release_ms: float


@dataclass(frozen=True)
class CanonicalSample:
    sample_id: str
    participant_id: str
    password_id: str
    source: str
    password: str
    keys: tuple[int, ...]
    press_times_ms: tuple[float, ...]
    release_times_ms: tuple[float, ...]
    dwell_times_ms: tuple[float, ...]
    flight_times_ms: tuple[float, ...]
    press_to_press_times_ms: tuple[float, ...]
    digraphs: tuple[DigraphTiming, ...]
    total_typing_duration_ms: float
    static_features: StaticFeatures
    guess_count: float | None
    log10_guesses: float | None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def sequence_length(self) -> int:
        return len(self.keys)


@dataclass(frozen=True)
class RejectedSample:
    source_path: str
    reason: str


@dataclass
class DatasetLoadResult:
    samples: list[CanonicalSample] = field(default_factory=list)
    rejections: list[RejectedSample] = field(default_factory=list)
    detected_timing_unit: str = "milliseconds"
    canonical_timing_unit: str = "milliseconds"
