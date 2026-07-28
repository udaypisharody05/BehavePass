from typing import List
from app.schemas.session import SessionFeaturesSchema, StaticFeaturesSchema

def generate_behavioural_summary(
    session_features: SessionFeaturesSchema,
    static_features: StaticFeaturesSchema
) -> List[str]:
    """
    Generates transparent, cautious, threshold-based behavioural observations.
    STRICT COMPLIANCE: Describes ONLY observable typing characteristics.
    NEVER infers cognitive state, stress, anxiety, or fatigue.
    """
    observations: List[str] = []

    # 1. Corrections & Backspaces
    if session_features.backspace_count >= 4 or session_features.correction_burst_count >= 2:
        observations.append("Frequent corrections were observed during creation.")
    elif session_features.backspace_count > 0:
        observations.append("Occasional corrections were made.")

    # 2. Pauses & Hesitations (Requirement 3: Precise singular vs plural wording)
    if session_features.pause_count >= 2 or session_features.total_pause_duration >= 2000.0:
        observations.append("The typing session contained several long pauses.")
    elif session_features.pause_count == 1:
        observations.append("One long pause was recorded during entry.")

    # 3. Flight Time / Inter-key Latency Variation
    if session_features.flight_time_std > 150.0 or session_features.dwell_time_std > 50.0:
        observations.append("The intervals between keystrokes varied considerably.")
    else:
        observations.append("The typing rhythm was relatively consistent.")

    # 4. Typing Pacing
    if session_features.characters_per_second >= 4.5:
        observations.append("A high typing pace was measured.")
    elif session_features.characters_per_second <= 1.5 and session_features.total_typing_duration > 3000:
        observations.append("A measured, deliberate typing pace was observed.")

    if not observations:
        observations.append("Standard typing characteristics recorded.")

    return observations

def map_zxcvbn_tier(score: int) -> str:
    tiers = {
        0: "Very Weak",
        1: "Weak",
        2: "Moderate",
        3: "Strong",
        4: "Very Strong"
    }
    return tiers.get(score, "Unknown")
