import io
import json
from typing import List, Optional
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.participant import Participant
from app.models.session import SessionModel
from app.models.keystroke import KeystrokeFeatureModel
from app.schemas.session import CreateSessionPayload, SessionSummaryResponse, AnalyticsSummaryResponse, SessionResponse

class SessionService:

    @staticmethod
    def get_or_create_participant(db: Session, participant_code: str) -> Participant:
        participant = db.query(Participant).filter(Participant.participant_code == participant_code).first()
        if not participant:
            participant = Participant(participant_code=participant_code)
            db.add(participant)
            db.commit()
            db.refresh(participant)
        return participant

    @classmethod
    def create_session(cls, db: Session, payload: CreateSessionPayload) -> SessionResponse:
        participant = cls.get_or_create_participant(db, payload.participant_code)

        session_obj = SessionModel(
            participant_id=participant.id,
            task_id=payload.task_id,
            task_type=payload.task_type,
            attempt_number=payload.attempt_number,
            condition=payload.condition,
            timed_limit_ms=payload.timed_limit_ms,
            completed_within_limit=payload.completed_within_limit,
            timed_out=payload.timed_out,
            pause_threshold_ms=payload.pause_threshold_ms,
            collector_version=payload.collector_version,
            feature_schema_version=payload.feature_schema_version,
            consent_version=payload.consent_version,
            is_valid=payload.is_valid,
            invalid_reason=payload.invalid_reason,
            device_type=payload.device_type,
            
            # Static Features
            password_length=payload.static_features.password_length,
            lowercase_count=payload.static_features.lowercase_count,
            uppercase_count=payload.static_features.uppercase_count,
            digit_count=payload.static_features.digit_count,
            symbol_count=payload.static_features.symbol_count,
            unique_character_count=payload.static_features.unique_character_count,
            repeated_character_count=payload.static_features.repeated_character_count,
            repeated_substring_count=payload.static_features.repeated_substring_count,
            sequential_character_count=payload.static_features.sequential_character_count,
            zxcvbn_score=payload.static_features.zxcvbn_score,
            log10_estimated_guesses=payload.static_features.log10_estimated_guesses,
            empirical_character_entropy=payload.static_features.empirical_character_entropy,
            character_pool_entropy_estimate=payload.static_features.character_pool_entropy_estimate,

            # Session Timing Features
            total_typing_duration=payload.session_features.total_typing_duration,
            total_key_presses=payload.session_features.total_key_presses,
            average_dwell_time=payload.session_features.average_dwell_time,
            dwell_time_std=payload.session_features.dwell_time_std,
            average_flight_time=payload.session_features.average_flight_time,
            flight_time_std=payload.session_features.flight_time_std,
            average_press_latency=payload.session_features.average_press_latency,
            longest_interkey_delay=payload.session_features.longest_interkey_delay,
            pause_count=payload.session_features.pause_count,
            total_pause_duration=payload.session_features.total_pause_duration,
            backspace_count=payload.session_features.backspace_count,
            backspace_rate=payload.session_features.backspace_rate,
            correction_burst_count=payload.session_features.correction_burst_count,
            characters_per_second=payload.session_features.characters_per_second,

            # Experimental behavioral inference
            behavioural_model_status=payload.behavioural_model_status,
            fusion_log10_estimated_guesses=payload.fusion_log10_estimated_guesses,
        )
        db.add(session_obj)
        db.flush()

        # Add sequence records
        for k in payload.keystroke_sequence:
            keystroke_obj = KeystrokeFeatureModel(
                session_id=session_obj.id,
                sequence_index=k.sequence_index,
                dwell_time=k.dwell_time,
                flight_time=k.flight_time,
                press_to_press_latency=k.press_to_press_latency,
                is_backspace=k.is_backspace,
                is_pause=k.is_pause
            )
            db.add(keystroke_obj)

        db.commit()
        db.refresh(session_obj)
        return cls.format_session_response(session_obj)

    @classmethod
    def get_session_by_id(cls, db: Session, session_id: str) -> Optional[SessionResponse]:
        session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session_obj:
            return None
        return cls.format_session_response(session_obj)

    @classmethod
    def format_session_response(cls, session_obj: SessionModel) -> SessionResponse:
        return SessionResponse(
            id=session_obj.id,
            participant_id=session_obj.participant_id,
            participant_code=session_obj.participant.participant_code if session_obj.participant else "",
            task_id=session_obj.task_id,
            task_type=session_obj.task_type,
            attempt_number=session_obj.attempt_number,
            condition=session_obj.condition,
            timed_limit_ms=session_obj.timed_limit_ms,
            completed_within_limit=session_obj.completed_within_limit,
            timed_out=session_obj.timed_out,
            pause_threshold_ms=session_obj.pause_threshold_ms,
            collector_version=session_obj.collector_version,
            feature_schema_version=session_obj.feature_schema_version,
            consent_version=session_obj.consent_version,
            is_valid=session_obj.is_valid,
            invalid_reason=session_obj.invalid_reason,
            device_type=session_obj.device_type,
            created_at=session_obj.created_at,
            behavioural_model_status=session_obj.behavioural_model_status,
            fusion_log10_estimated_guesses=session_obj.fusion_log10_estimated_guesses,
            static_features={
                "password_length": session_obj.password_length,
                "lowercase_count": session_obj.lowercase_count,
                "uppercase_count": session_obj.uppercase_count,
                "digit_count": session_obj.digit_count,
                "symbol_count": session_obj.symbol_count,
                "unique_character_count": session_obj.unique_character_count,
                "repeated_character_count": session_obj.repeated_character_count,
                "repeated_substring_count": session_obj.repeated_substring_count,
                "sequential_character_count": session_obj.sequential_character_count,
                "zxcvbn_score": session_obj.zxcvbn_score,
                "log10_estimated_guesses": session_obj.log10_estimated_guesses,
                "empirical_character_entropy": session_obj.empirical_character_entropy,
                "character_pool_entropy_estimate": session_obj.character_pool_entropy_estimate,
            },
            session_features={
                "total_typing_duration": session_obj.total_typing_duration,
                "total_key_presses": session_obj.total_key_presses,
                "average_dwell_time": session_obj.average_dwell_time,
                "dwell_time_std": session_obj.dwell_time_std,
                "average_flight_time": session_obj.average_flight_time,
                "flight_time_std": session_obj.flight_time_std,
                "average_press_latency": session_obj.average_press_latency,
                "longest_interkey_delay": session_obj.longest_interkey_delay,
                "pause_count": session_obj.pause_count,
                "total_pause_duration": session_obj.total_pause_duration,
                "backspace_count": session_obj.backspace_count,
                "backspace_rate": session_obj.backspace_rate,
                "correction_burst_count": session_obj.correction_burst_count,
                "characters_per_second": session_obj.characters_per_second,
            },
            keystroke_sequence=[
                {
                    "sequence_index": k.sequence_index,
                    "dwell_time": k.dwell_time,
                    "flight_time": k.flight_time,
                    "press_to_press_latency": k.press_to_press_latency,
                    "is_backspace": k.is_backspace,
                    "is_pause": k.is_pause,
                }
                for k in sorted(session_obj.keystrokes or [], key=lambda item: item.sequence_index)
            ]
        )

    @staticmethod
    def list_session_summaries(db: Session, skip: int = 0, limit: int = 100) -> List[SessionSummaryResponse]:
        results = db.query(
            SessionModel.id,
            Participant.participant_code,
            SessionModel.task_id,
            SessionModel.condition,
            SessionModel.completed_within_limit,
            SessionModel.timed_out,
            SessionModel.is_valid,
            SessionModel.password_length,
            SessionModel.zxcvbn_score,
            SessionModel.log10_estimated_guesses,
            SessionModel.behavioural_model_status,
            SessionModel.fusion_log10_estimated_guesses,
            SessionModel.total_typing_duration,
            SessionModel.pause_count,
            SessionModel.backspace_count,
            SessionModel.created_at
        ).join(Participant, SessionModel.participant_id == Participant.id)\
         .order_by(SessionModel.created_at.desc())\
         .offset(skip).limit(limit).all()

        return [
            SessionSummaryResponse(
                id=r.id,
                participant_code=r.participant_code,
                task_id=r.task_id,
                condition=r.condition,
                completed_within_limit=r.completed_within_limit,
                timed_out=r.timed_out,
                is_valid=r.is_valid,
                password_length=r.password_length,
                zxcvbn_score=r.zxcvbn_score,
                log10_estimated_guesses=r.log10_estimated_guesses,
                behavioural_model_status=r.behavioural_model_status,
                fusion_log10_estimated_guesses=r.fusion_log10_estimated_guesses,
                total_typing_duration=r.total_typing_duration,
                pause_count=r.pause_count,
                backspace_count=r.backspace_count,
                created_at=r.created_at
            )
            for r in results
        ]

    @staticmethod
    def get_analytics_summary(db: Session) -> AnalyticsSummaryResponse:
        total_sessions = db.query(func.count(SessionModel.id)).scalar() or 0
        total_participants = (
            db.query(func.count(func.distinct(Participant.participant_code)))
            .join(SessionModel, SessionModel.participant_id == Participant.id)
            .scalar()
            or 0
        )
        timed_count = db.query(func.count(SessionModel.id)).filter(SessionModel.condition == "timed").scalar() or 0
        untimed_count = db.query(func.count(SessionModel.id)).filter(SessionModel.condition == "untimed").scalar() or 0
        valid_count = db.query(func.count(SessionModel.id)).filter(SessionModel.is_valid == True).scalar() or 0
        invalid_count = total_sessions - valid_count

        avg_duration = db.query(func.avg(SessionModel.total_typing_duration)).scalar() or 0.0
        avg_backspace = db.query(func.avg(SessionModel.backspace_count)).scalar() or 0.0
        avg_pause = db.query(func.avg(SessionModel.pause_count)).scalar() or 0.0
        avg_zxcvbn = db.query(func.avg(SessionModel.zxcvbn_score)).scalar() or 0.0

        return AnalyticsSummaryResponse(
            total_sessions=total_sessions,
            total_participants=total_participants,
            timed_session_count=timed_count,
            untimed_session_count=untimed_count,
            valid_session_count=valid_count,
            invalid_session_count=invalid_count,
            average_duration=round(float(avg_duration), 2),
            average_backspace_count=round(float(avg_backspace), 2),
            average_pause_count=round(float(avg_pause), 2),
            average_zxcvbn_score=round(float(avg_zxcvbn), 2)
        )

    @staticmethod
    def export_dataset_csv(db: Session) -> str:
        query = db.query(
            SessionModel.id.label("session_id"),
            Participant.participant_code,
            SessionModel.task_id,
            SessionModel.task_type,
            SessionModel.attempt_number,
            SessionModel.condition,
            SessionModel.timed_limit_ms,
            SessionModel.completed_within_limit,
            SessionModel.timed_out,
            SessionModel.is_valid,
            SessionModel.invalid_reason,
            SessionModel.device_type,
            SessionModel.pause_threshold_ms,
            SessionModel.collector_version,
            SessionModel.feature_schema_version,
            SessionModel.password_length,
            SessionModel.lowercase_count,
            SessionModel.uppercase_count,
            SessionModel.digit_count,
            SessionModel.symbol_count,
            SessionModel.unique_character_count,
            SessionModel.repeated_character_count,
            SessionModel.repeated_substring_count,
            SessionModel.sequential_character_count,
            SessionModel.zxcvbn_score,
            SessionModel.log10_estimated_guesses,
            SessionModel.behavioural_model_status,
            SessionModel.fusion_log10_estimated_guesses,
            SessionModel.empirical_character_entropy,
            SessionModel.character_pool_entropy_estimate,
            SessionModel.total_typing_duration,
            SessionModel.total_key_presses,
            SessionModel.average_dwell_time,
            SessionModel.dwell_time_std,
            SessionModel.average_flight_time,
            SessionModel.flight_time_std,
            SessionModel.average_press_latency,
            SessionModel.longest_interkey_delay,
            SessionModel.pause_count,
            SessionModel.total_pause_duration,
            SessionModel.backspace_count,
            SessionModel.backspace_rate,
            SessionModel.correction_burst_count,
            SessionModel.characters_per_second,
            SessionModel.created_at
        ).join(Participant, SessionModel.participant_id == Participant.id)

        df = pd.read_sql(query.statement, db.bind)
        sequence_rows = db.query(KeystrokeFeatureModel).order_by(
            KeystrokeFeatureModel.session_id,
            KeystrokeFeatureModel.sequence_index,
        ).all()
        sequences = {}
        for item in sequence_rows:
            sequences.setdefault(item.session_id, []).append({
                "sequence_index": item.sequence_index,
                "dwell_time": item.dwell_time,
                "flight_time": item.flight_time,
                "press_to_press_latency": item.press_to_press_latency,
                "is_backspace": item.is_backspace,
                "is_pause": item.is_pause,
            })
        df["keystroke_sequence_json"] = df["session_id"].map(
            lambda session_id: json.dumps(
                sequences.get(session_id, []), sort_keys=True, separators=(",", ":")
            )
        )
        output = io.StringIO()
        df.to_csv(output, index=False)
        return output.getvalue()

    @staticmethod
    def delete_session(db: Session, session_id: str) -> bool:
        session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session_obj:
            return False
        db.delete(session_obj)
        db.commit()
        return True
