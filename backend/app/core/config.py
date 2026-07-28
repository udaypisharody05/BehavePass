import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "BehavePass-Lite"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./behavepass.db")
    PAUSE_THRESHOLD_MS: float = 500.0
    COLLECTOR_VERSION: str = "1.0.0"
    FEATURE_SCHEMA_VERSION: str = "1.0.0"
    CONSENT_VERSION: str = "1.0.0"

settings = Settings()
