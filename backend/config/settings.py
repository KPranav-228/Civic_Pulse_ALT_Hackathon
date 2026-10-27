from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "News Summarizer"
    APP_VERSION: str = "1.0.0"
    # Avoid consuming an unrelated DEBUG variable from the host environment.
    DEBUG: bool = Field(default=False, validation_alias="NEWS_SUMMARIZER_DEBUG")
    GROQ_API_KEY: str = "" 
    GROQ_MODEL: str = "llama3-70b-8192"
    GROQ_MAX_RETRIES: int = 3
    GROQ_RETRY_DELAY: float = 3.0
    MAX_LOADED_MODELS: int = 1
    DEFAULT_MAX_LENGTH: int = 150
    DEFAULT_MIN_LENGTH: int = 30
    DEFAULT_NUM_BEAMS: int = 4
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    DATA_DIR: str = "data"
    OUTPUT_DIR: str = "outputs"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
