from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    GROQ_API_KEY: Optional[str] = None
    # Temporary fallback for compatibility with older .env files.
    GEMINI_API_KEY: Optional[str] = None
    MODEL_NAME: str = "llama-3.1-8b-instant"
    
    # Retry settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
