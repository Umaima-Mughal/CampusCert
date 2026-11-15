"""Settings for the AI paper generator (Groq).

Kept inside backend/app/ai/ so the shared core/config.py is not touched.
Reads the same root .env file as the rest of the app.
"""
from pathlib import Path

from pydantic_settings import BaseSettings

_ENV_FILE_PATH = Path(__file__).resolve().parents[3] / ".env"

DEFAULT_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class AISettings(BaseSettings):
    # Put your free key from https://console.groq.com/keys in GROQ_API_KEY
    # (LLM_API_KEY / LLM_API_URL from the original .env.example also work).
    GROQ_API_KEY: str = ""
    LLM_API_KEY: str = ""
    LLM_API_URL: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_FALLBACK_MODEL: str = "llama-3.1-8b-instant"
    AI_MAX_QUESTIONS: int = 40       # hard cap per paper
    AI_BATCH_SIZE: int = 8           # questions asked per Groq call (keeps free-tier token limits happy)
    AI_TIMEOUT_SECONDS: float = 60.0

    class Config:
        env_file = _ENV_FILE_PATH
        case_sensitive = True
        extra = "ignore"

    @property
    def api_key(self) -> str:
        return (self.GROQ_API_KEY or self.LLM_API_KEY).strip()

    @property
    def api_url(self) -> str:
        return self.LLM_API_URL.strip() or DEFAULT_GROQ_URL


def get_ai_settings() -> AISettings:
    return AISettings()
