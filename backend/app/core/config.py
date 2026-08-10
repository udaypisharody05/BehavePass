import os
from pathlib import Path

from pydantic import BaseModel


BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = f"sqlite:///{(BACKEND_DIR / 'behavepass.db').as_posix()}"


class Settings(BaseModel):
    PROJECT_NAME: str = "BehavePass-Lite"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    DATABASE_URL: str = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    PAUSE_THRESHOLD_MS: float = 500.0
    COLLECTOR_VERSION: str = "1.0.0"
    FEATURE_SCHEMA_VERSION: str = "1.0.0"
    CONSENT_VERSION: str = "1.0.0"

settings = Settings()
