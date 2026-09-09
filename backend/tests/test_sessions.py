import csv
import io
import json
from copy import deepcopy

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text

from app.database.migrations import ensure_session_behavioral_columns
from app.main import app

client = TestClient(app)

def test_session_lifecycle_and_endpoints():
    payload = {
        "participant_code": "TEST-PART-01",
        "task_id": "TASK-TEST",
        "task_type": "creation",
        "attempt_number": 1,
        "condition": "untimed",
        "timed_limit_ms": None,
        "completed_within_limit": None,
        "timed_out": False,
        "pause_threshold_ms": 500.0,
        "collector_version": "1.0.0",
        "feature_schema_version": "1.0.0",
        "consent_version": "1.0.0",
        "is_valid": True,
        "invalid_reason": None,
        "device_type": "desktop",
        "behavioural_model_status": "ready_synthetic_proof_of_concept",
        "fusion_log10_estimated_guesses": 7.125,
        "static_features": {
            "password_length": 10,
            "lowercase_count": 5,
            "uppercase_count": 2,
            "digit_count": 2,
            "symbol_count": 1,
            "unique_character_count": 8,
            "repeated_character_count": 2,
            "repeated_substring_count": 0,
            "sequential_character_count": 0,
            "zxcvbn_score": 3,
            "log10_estimated_guesses": 6.8,
            "empirical_character_entropy": 3.1,
            "character_pool_entropy_estimate": 55.4
        },
        "session_features": {
            "total_typing_duration": 2200.0,
            "total_key_presses": 10,
            "average_dwell_time": 85.0,
            "dwell_time_std": 12.0,
            "average_flight_time": 135.0,
            "flight_time_std": 25.0,
            "average_press_latency": 220.0,
            "longest_interkey_delay": 580.0,
            "pause_count": 1,
            "total_pause_duration": 580.0,
            "backspace_count": 0,
            "backspace_rate": 0.0,
            "correction_burst_count": 0,
            "characters_per_second": 4.54
        },
        "keystroke_sequence": [
            {
                "sequence_index": 0,
                "dwell_time": 85.0,
                "flight_time": None, # First event flight_time represented as null
                "press_to_press_latency": None, # First event press_to_press_latency represented as null
                "is_backspace": False,
                "is_pause": False
            }
        ]
    }

    # 1. Create session
    res = client.post("/api/sessions", json=payload)
    assert res.status_code == 201
    created_data = res.json()
    session_id = created_data["id"]
    assert "participant_id" in created_data
    assert created_data["keystroke_sequence"][0]["flight_time"] is None
    assert created_data["keystroke_sequence"][0]["press_to_press_latency"] is None
    assert created_data["behavioural_model_status"] == "ready_synthetic_proof_of_concept"
    assert created_data["fusion_log10_estimated_guesses"] == 7.125

    # 2. Get session by ID
    res_get = client.get(f"/api/sessions/{session_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == session_id
    assert res_get.json()["fusion_log10_estimated_guesses"] == 7.125

    # 3. List summaries
    res_list = client.get("/api/sessions")
    assert res_list.status_code == 200
    summaries = res_list.json()
    assert len(summaries) >= 1
    stored_summary = next(item for item in summaries if item["id"] == session_id)
    assert stored_summary["behavioural_model_status"] == "ready_synthetic_proof_of_concept"
    assert stored_summary["fusion_log10_estimated_guesses"] == 7.125

    # 4. Get analytics
    res_analytics = client.get("/api/analytics/summary")
    assert res_analytics.status_code == 200
    analytics = res_analytics.json()
    assert analytics["total_sessions"] >= 1

    # 5. Export CSV
    res_export = client.get("/api/export/csv")
    assert res_export.status_code == 200
    assert "session_id" in res_export.text
    assert "log10_estimated_guesses" in res_export.text
    assert "completed_within_limit" in res_export.text
    exported_rows = list(csv.DictReader(io.StringIO(res_export.text)))
    exported = next(row for row in exported_rows if row["session_id"] == session_id)
    assert exported["behavioural_model_status"] == "ready_synthetic_proof_of_concept"
    assert float(exported["fusion_log10_estimated_guesses"]) == 7.125
    assert float(exported["average_dwell_time"]) == 85.0
    sequence = json.loads(exported["keystroke_sequence_json"])
    assert sequence == [{
        "dwell_time": 85.0,
        "flight_time": None,
        "is_backspace": False,
        "is_pause": False,
        "press_to_press_latency": None,
        "sequence_index": 0,
    }]
    assert "Secret123!" not in res_export.text
    assert "key_char" not in exported["keystroke_sequence_json"]

    # 6. Predict endpoint
    predict_req = {
        "static_features": payload["static_features"],
        "session_features": payload["session_features"]
    }
    res_predict = client.post("/api/predict", json=predict_req)
    assert res_predict.status_code == 200
    predict_data = res_predict.json()
    assert predict_data["behavioural_model_status"] == "sequence_unavailable"
    assert predict_data["fusion_log10_estimated_guesses"] is None
    assert predict_data["warnings"]
    assert len(predict_data["behavioural_summary"]) > 0

    # 7. Model-unavailable and historical sessions remain storable with null output.
    unavailable_payload = deepcopy(payload)
    unavailable_payload["task_id"] = "TASK-MODEL-UNAVAILABLE"
    unavailable_payload["behavioural_model_status"] = "model_unavailable"
    unavailable_payload["fusion_log10_estimated_guesses"] = None
    unavailable = client.post("/api/sessions", json=unavailable_payload)
    assert unavailable.status_code == 201
    unavailable_id = unavailable.json()["id"]
    assert unavailable.json()["behavioural_model_status"] == "model_unavailable"
    assert unavailable.json()["fusion_log10_estimated_guesses"] is None

    historical_payload = deepcopy(payload)
    historical_payload["task_id"] = "TASK-HISTORICAL"
    historical_payload.pop("behavioural_model_status")
    historical_payload.pop("fusion_log10_estimated_guesses")
    historical = client.post("/api/sessions", json=historical_payload)
    assert historical.status_code == 201
    historical_id = historical.json()["id"]
    assert historical.json()["behavioural_model_status"] is None
    assert historical.json()["fusion_log10_estimated_guesses"] is None

    # Participant analytics count distinct codes represented by stored sessions,
    # not orphaned participant rows or the number of sessions.
    all_summaries = client.get("/api/sessions?limit=1000").json()
    analytics = client.get("/api/analytics/summary").json()
    assert analytics["total_participants"] == len({
        summary["participant_code"] for summary in all_summaries
    })

    # 8. Delete test sessions
    for stored_id in (session_id, unavailable_id, historical_id):
        res_del = client.delete(f"/api/sessions/{stored_id}")
        assert res_del.status_code == 204


def test_existing_sqlite_database_gets_nullable_behavioral_columns(tmp_path):
    database_path = tmp_path / "historical.db"
    migration_engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    with migration_engine.begin() as connection:
        connection.execute(text("CREATE TABLE sessions (id VARCHAR(36) PRIMARY KEY)"))
        connection.execute(text("INSERT INTO sessions (id) VALUES ('historical-session')"))

    ensure_session_behavioral_columns(migration_engine)
    ensure_session_behavioral_columns(migration_engine)

    column_names = {
        column["name"] for column in inspect(migration_engine).get_columns("sessions")
    }
    assert "behavioural_model_status" in column_names
    assert "fusion_log10_estimated_guesses" in column_names
    with migration_engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT behavioural_model_status, fusion_log10_estimated_guesses "
                "FROM sessions WHERE id = 'historical-session'"
            )
        ).one()
    assert row == (None, None)
