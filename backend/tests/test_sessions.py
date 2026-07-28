from fastapi.testclient import TestClient
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

    # 2. Get session by ID
    res_get = client.get(f"/api/sessions/{session_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == session_id

    # 3. List summaries
    res_list = client.get("/api/sessions")
    assert res_list.status_code == 200
    summaries = res_list.json()
    assert len(summaries) >= 1

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

    # 6. Predict endpoint
    predict_req = {
        "static_features": payload["static_features"],
        "session_features": payload["session_features"]
    }
    res_predict = client.post("/api/predict", json=predict_req)
    assert res_predict.status_code == 200
    predict_data = res_predict.json()
    assert predict_data["behavioural_model_status"] == "not_trained"
    assert len(predict_data["behavioural_summary"]) > 0

    # 7. Delete session
    res_del = client.delete(f"/api/sessions/{session_id}")
    assert res_del.status_code == 204
