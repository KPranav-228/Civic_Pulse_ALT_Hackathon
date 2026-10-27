"""
CivicPulse server configuration.

Loads settings from a .env file using pydantic-settings.
All configuration values can be overridden via environment variables.
"""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    GEMINI_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./civicpulse.db"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RANDOM_SEED: int = 42
    MODEL_DIR: str = "server/models"
    REPORTS_DIR: str = "reports"
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    RATE_LIMIT: str = "60/minute"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
