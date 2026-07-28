from app.schemas.session import CreateSessionPayload
from app.services.feature_validator import FeatureValidator
from app.models.session import SessionModel

def test_no_password_field_in_schemas():
    """Verify that CreateSessionPayload fields do not contain 'password', 'plaintext', or raw key names."""
    schema_fields = list(CreateSessionPayload.model_fields.keys())
    assert "password" not in schema_fields
    assert "plaintext" not in schema_fields
    assert "raw_keys" not in schema_fields
    assert "key_char" not in schema_fields

def test_feature_validator_rejects_forbidden_keys():
    """Verify FeatureValidator flags payload if forbidden sensitive key names are present."""
    invalid_payload = {
        "participant_code": "PART-001",
        "plaintext": "Secret123!",
        "password": "Secret123!"
    }
    valid, msg = FeatureValidator.validate_payload(invalid_payload)
    assert not valid
    assert "Forbidden key" in msg

def test_orm_model_has_no_plaintext_columns():
    """Assert SessionModel SQLAlchemy table columns contain no password/plaintext columns."""
    col_names = [col.name for col in SessionModel.__table__.columns]
    assert "password" not in col_names
    assert "plaintext" not in col_names
    assert "raw_keys" not in col_names
    assert "password_text" not in col_names
