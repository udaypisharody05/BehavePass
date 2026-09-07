TARGET = "log10_estimated_guesses"

METADATA_COLUMNS = [
    "session_id",
    "source",
    "synthetic_seed",
    "participant_code",
    "typing_profile",
    "task_type",
    "pause_threshold_ms",
]

STATIC_FEATURES = [
    "password_length",
    "lowercase_count",
    "uppercase_count",
    "digit_count",
    "symbol_count",
    "unique_character_count",
    "repeated_character_count",
    "repeated_substring_count",
    "sequential_character_count",
    "empirical_character_entropy",
    "character_pool_entropy_estimate",
]

# zxcvbn_score is emitted by the same zxcvbn call that emits the target's
# guess count. It is retained only for explicitly labelled leakage comparisons.
TARGET_ADJACENT_FEATURES = ["zxcvbn_score"]

BEHAVIORAL_FEATURES = [
    "total_typing_duration",
    "total_key_presses",
    "average_dwell_time",
    "dwell_time_std",
    "average_flight_time",
    "flight_time_std",
    "average_press_latency",
    "longest_interkey_delay",
    "pause_count",
    "total_pause_duration",
    "backspace_count",
    "backspace_rate",
    "correction_burst_count",
    "characters_per_second",
]

FEATURE_GROUPS = {
    "static_with_zxcvbn": STATIC_FEATURES + TARGET_ADJACENT_FEATURES,
    "static_safe": STATIC_FEATURES,
    "behavioral": BEHAVIORAL_FEATURES,
    "combined_safe": STATIC_FEATURES + BEHAVIORAL_FEATURES,
    "combined_with_zxcvbn": STATIC_FEATURES + BEHAVIORAL_FEATURES + TARGET_ADJACENT_FEATURES,
}


def validate_feature_groups(columns: set[str]) -> None:
    required = set(METADATA_COLUMNS + STATIC_FEATURES + TARGET_ADJACENT_FEATURES + BEHAVIORAL_FEATURES + [TARGET])
    missing = required - columns
    if missing:
        raise ValueError(f"dataset is missing expected columns: {sorted(missing)}")
    for name, features in FEATURE_GROUPS.items():
        if TARGET in features:
            raise ValueError(f"target leaked into feature group {name}")
        overlap = set(features) & set(METADATA_COLUMNS)
        if overlap:
            raise ValueError(f"metadata leaked into feature group {name}: {sorted(overlap)}")
