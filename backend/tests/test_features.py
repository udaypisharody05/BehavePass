from app.schemas.session import KeystrokeFeatureItem, CreateSessionPayload, StaticFeaturesSchema, SessionFeaturesSchema

def test_negative_flight_time_permitted():
    """Requirement 5: Confirm negative flight time is permitted for overlapping keypresses."""
    item = KeystrokeFeatureItem(
        sequence_index=1,
        dwell_time=90.0,
        flight_time=-15.5,  # Negative flight time for key overlap
        press_to_press_latency=74.5,
        is_backspace=False,
        is_pause=False
    )
    assert item.flight_time < 0.0

def test_session_metadata_and_validity_fields():
    """Requirement 8 & 13: Confirm extended metadata and validity status fields are preserved."""
    static_feat = StaticFeaturesSchema(
        password_length=8,
        lowercase_count=4,
        uppercase_count=2,
        digit_count=2,
        symbol_count=0,
        unique_character_count=6,
        repeated_character_count=2,
        repeated_substring_count=0,
        sequential_character_count=1,
        zxcvbn_score=2,
        log10_estimated_guesses=4.5,
        empirical_character_entropy=2.8,
        character_pool_entropy_estimate=48.0
    )
    
    session_feat = SessionFeaturesSchema(
        total_typing_duration=2500.0,
        total_key_presses=8,
        average_dwell_time=80.0,
        dwell_time_std=10.0,
        average_flight_time=120.0,
        flight_time_std=20.0,
        average_press_latency=200.0,
        longest_interkey_delay=550.0,
        pause_count=1,
        total_pause_duration=550.0,
        backspace_count=0,
        backspace_rate=0.0,
        correction_burst_count=0,
        characters_per_second=3.2
    )

    payload = CreateSessionPayload(
        participant_code="PART-100",
        task_id="TASK-01",
        task_type="creation",
        attempt_number=1,
        condition="timed",
        timed_limit_ms=15000.0,
        pause_threshold_ms=500.0,
        collector_version="1.0.0",
        feature_schema_version="1.0.0",
        consent_version="1.0.0",
        is_valid=False,
        invalid_reason="Paste detected without keystrokes",
        device_type="desktop",
        static_features=static_feat,
        session_features=session_feat,
        keystroke_sequence=[]
    )

    assert payload.feature_schema_version == "1.0.0"
    assert payload.is_valid is False
    assert payload.invalid_reason == "Paste detected without keystrokes"
