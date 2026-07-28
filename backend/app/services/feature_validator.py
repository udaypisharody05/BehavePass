import math
from typing import Dict, Any, Tuple
from app.schemas.session import CreateSessionPayload

class FeatureValidator:
    """
    Validates incoming numeric features and metadata.
    Guarantees backend NEVER handles plaintext passwords or raw key identifiers.
    """
    
    FORBIDDEN_KEYS = {"password", "plaintext", "raw_keys", "key_char", "secret", "hash"}

    @classmethod
    def validate_payload(cls, payload_dict: Dict[str, Any]) -> Tuple[bool, str]:
        # 1. Reject any dictionary containing forbidden sensitive key names
        found_forbidden = cls._check_forbidden_keys(payload_dict)
        if found_forbidden:
            return False, f"Forbidden key detected in payload: {found_forbidden}"

        # 2. Check numeric value sanity
        is_finite, msg = cls._check_numeric_finiteness(payload_dict)
        if not is_finite:
            return False, msg

        return True, "Payload valid"

    @classmethod
    def _check_forbidden_keys(cls, data: Any) -> str:
        if isinstance(data, dict):
            for k, v in data.items():
                if k.lower() in cls.FORBIDDEN_KEYS:
                    return k
                res = cls._check_forbidden_keys(v)
                if res:
                    return res
        elif isinstance(data, list):
            for item in data:
                res = cls._check_forbidden_keys(item)
                if res:
                    return res
        return ""

    @classmethod
    def _check_numeric_finiteness(cls, data: Any) -> Tuple[bool, str]:
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    if math.isnan(v) or math.isinf(v):
                        return False, f"Non-finite numeric value in key '{k}': {v}"
                elif isinstance(v, (dict, list)):
                    ok, msg = cls._check_numeric_finiteness(v)
                    if not ok:
                        return False, msg
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                if isinstance(item, (int, float)) and not isinstance(item, bool):
                    if math.isnan(item) or math.isinf(item):
                        return False, f"Non-finite numeric value at index {idx}: {item}"
                elif isinstance(item, (dict, list)):
                    ok, msg = cls._check_numeric_finiteness(item)
                    if not ok:
                        return False, msg
        return True, "OK"
