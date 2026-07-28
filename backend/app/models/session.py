import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base

class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
    
    # Metadata
    task_id = Column(String(64), nullable=False)
    task_type = Column(String(64), nullable=False)
    attempt_number = Column(Integer, default=1)
    condition = Column(String(32), nullable=False) # 'timed' | 'untimed'
    timed_limit_ms = Column(Float, nullable=True)
    completed_within_limit = Column(Boolean, nullable=True)
    timed_out = Column(Boolean, nullable=False, default=False)
    pause_threshold_ms = Column(Float, nullable=False, default=500.0)
    collector_version = Column(String(32), nullable=False)
    feature_schema_version = Column(String(32), nullable=False)
    consent_version = Column(String(32), nullable=False)
    is_valid = Column(Boolean, nullable=False, default=True)
    invalid_reason = Column(String(255), nullable=True)
    device_type = Column(String(64), nullable=False, default="desktop")

    # Static Password Features (Zero Plaintext stored!)
    password_length = Column(Integer, nullable=False)
    lowercase_count = Column(Integer, nullable=False)
    uppercase_count = Column(Integer, nullable=False)
    digit_count = Column(Integer, nullable=False)
    symbol_count = Column(Integer, nullable=False)
    unique_character_count = Column(Integer, nullable=False)
    repeated_character_count = Column(Integer, nullable=False)
    repeated_substring_count = Column(Integer, nullable=False)
    sequential_character_count = Column(Integer, nullable=False)
    zxcvbn_score = Column(Integer, nullable=False)
    log10_estimated_guesses = Column(Float, nullable=False)
    empirical_character_entropy = Column(Float, nullable=False)
    character_pool_entropy_estimate = Column(Float, nullable=False)

    # Session Timing Features
    total_typing_duration = Column(Float, nullable=False)
    total_key_presses = Column(Integer, nullable=False)
    average_dwell_time = Column(Float, nullable=False)
    dwell_time_std = Column(Float, nullable=False)
    average_flight_time = Column(Float, nullable=False)
    flight_time_std = Column(Float, nullable=False)
    average_press_latency = Column(Float, nullable=False)
    longest_interkey_delay = Column(Float, nullable=False)
    pause_count = Column(Integer, nullable=False)
    total_pause_duration = Column(Float, nullable=False)
    backspace_count = Column(Integer, nullable=False)
    backspace_rate = Column(Float, nullable=False)
    correction_burst_count = Column(Integer, nullable=False)
    characters_per_second = Column(Float, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    participant = relationship("Participant", back_populates="sessions")
    keystrokes = relationship("KeystrokeFeatureModel", back_populates="session", cascade="all, delete-orphan")
