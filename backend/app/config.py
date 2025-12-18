from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://bookwhisperer:bookwhisperer_password@localhost:5432/bookwhisperer"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Ollama
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"
    OLLAMA_MAX_TOKENS: int = 4000  # Max tokens per LLM request

    # Chatterbox TTS
    CHATTERBOX_URL: str = "http://localhost:4123"
    TTS_MAX_CHUNK_SIZE: int = 5000  # Max characters per TTS request

    # Storage
    UPLOAD_STORAGE_PATH: str = "storage/uploads"
    AUDIO_STORAGE_PATH: str = "storage/audio"
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "BookWhisperer"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Global settings instance
settings = get_settings()
