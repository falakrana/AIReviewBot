from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # --- LLM ---
    GROQ_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None          # legacy fallback
    MODEL_NAME: str = "llama-3.1-8b-instant"
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2

    # --- Redis (broker + cache) ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 86400                        # seconds (24 h)

    # --- Database (SQLite default, swap to PostgreSQL DSN) ---
    DATABASE_URL: str = "sqlite:///./storage/aireviewbot.db"

    # --- Celery ---
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # --- Parallel Processing ---
    MAX_PARALLEL_CHUNKS: int = 5

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
