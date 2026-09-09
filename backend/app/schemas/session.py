from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class KeystrokeFeatureItem(BaseModel):
    sequence_index: int
    dwell_time: float
    flight_time: Optional[float] = None
    press_to_press_latency: Optional[float] = None
    is_backspace: bool
    is_pause: bool

class StaticFeaturesSchema(BaseModel):
    password_length: int = Field(..., ge=1)
    lowercase_count: int = Field(..., ge=0)
    uppercase_count: int = Field(..., ge=0)
    digit_count: int = Field(..., ge=0)
    symbol_count: int = Field(..., ge=0)
    unique_character_count: int = Field(..., ge=0)
    repeated_character_count: int = Field(..., ge=0)
    repeated_substring_count: int = Field(..., ge=0)
    sequential_character_count: int = Field(..., ge=0)
    zxcvbn_score: int = Field(..., ge=0, le=4)
    log10_estimated_guesses: float = Field(..., ge=0.0)
    empirical_character_entropy: float = Field(..., ge=0.0)
    character_pool_entropy_estimate: float = Field(..., ge=0.0)

class SessionFeaturesSchema(BaseModel):
    total_typing_duration: float = Field(..., ge=0.0)
    total_key_presses: int = Field(..., ge=0)
    average_dwell_time: float = Field(..., ge=0.0)
    dwell_time_std: float = Field(..., ge=0.0)
    average_flight_time: float
    flight_time_std: float = Field(..., ge=0.0)
    average_press_latency: float = Field(..., ge=0.0)
    longest_interkey_delay: float = Field(..., ge=0.0)
    pause_count: int = Field(..., ge=0)
    total_pause_duration: float = Field(..., ge=0.0)
    backspace_count: int = Field(..., ge=0)
    backspace_rate: float = Field(..., ge=0.0)
    correction_burst_count: int = Field(..., ge=0)
    characters_per_second: float = Field(..., ge=0.0)

class CreateSessionPayload(BaseModel):
    participant_code: str = Field(..., min_length=2, max_length=64)
    task_id: str = Field(..., min_length=1, max_length=64)
    task_type: str = Field(..., min_length=1, max_length=64)
    attempt_number: int = Field(1, ge=1)
    condition: str = Field(..., pattern="^(timed|untimed)$")
    timed_limit_ms: Optional[float] = None
    completed_within_limit: Optional[bool] = None
    timed_out: bool = False
    pause_threshold_ms: float = Field(500.0, gt=0)
    collector_version: str = "1.0.0"
    feature_schema_version: str = "1.0.0"
    consent_version: str = "1.0.0"
    is_valid: bool = True
    invalid_reason: Optional[str] = None
    device_type: str = "desktop"
    
    static_features: StaticFeaturesSchema
    session_features: SessionFeaturesSchema
    keystroke_sequence: List[KeystrokeFeatureItem]
    behavioural_model_status: Optional[str] = Field(None, max_length=64)
    fusion_log10_estimated_guesses: Optional[float] = None

class SessionResponse(CreateSessionPayload):
    id: str
    participant_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SessionSummaryResponse(BaseModel):
    id: str
    participant_code: str
    task_id: str
    condition: str
    completed_within_limit: Optional[bool] = None
    timed_out: bool = False
    is_valid: bool
    password_length: int
    zxcvbn_score: int
    log10_estimated_guesses: float
    behavioural_model_status: Optional[str] = None
    fusion_log10_estimated_guesses: Optional[float] = None
    total_typing_duration: float
    pause_count: int
    backspace_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AnalyticsSummaryResponse(BaseModel):
    total_sessions: int
    total_participants: int
    timed_session_count: int
    untimed_session_count: int
    valid_session_count: int
    invalid_session_count: int
    average_duration: float
    average_backspace_count: float
    average_pause_count: float
    average_zxcvbn_score: float

class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    static_features: StaticFeaturesSchema
    session_features: SessionFeaturesSchema
    keystroke_sequence: List[KeystrokeFeatureItem] = Field(default_factory=list)

class PredictResponse(BaseModel):
    static_strength_tier: str
    zxcvbn_score: int
    log10_estimated_guesses: float
    behavioural_summary: List[str]
    behavioural_model_status: str = "not_trained"
    fusion_log10_estimated_guesses: Optional[float] = None
    model_used: str = "Static analysis only"
    model_type: str = "BiLSTM + MLP fusion"
    target: str = "log10 estimated guesses"
    warnings: List[str] = Field(default_factory=list)
