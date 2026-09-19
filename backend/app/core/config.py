"""
app/core/config.py

Central place for all app settings.
Reads values from environment variables (which come from your .env file).
Everyone else in the team imports `settings` from here instead of
hardcoding things like DB URLs or secret keys.
"""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache

# Always point at backend/.env, no matter which folder a command is run
# from (repo root, backend/, database/, etc.) — this fixes the common
# "it works when I run uvicorn but not when I run alembic" issue.
_ENV_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")


class Settings(BaseSettings):
    # --- App info ---
    APP_NAME: str = "CampusCert"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/campuscert"

    # --- Auth / JWT ---
    JWT_SECRET_KEY: str = "change-this-in-.env"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60          # short-lived login token
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7             # longer-lived refresh token

    # --- CORS (so the frontend on a different port can talk to this API) ---
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = _ENV_FILE_PATH
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """
    Cached so we don't re-read the .env file on every single request.
    Usage elsewhere:  from app.core.config import get_settings
                       settings = get_settings()
    """
    return Settings()


settings = get_settings()
