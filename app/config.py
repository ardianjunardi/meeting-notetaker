from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    secret_key: str = "change-me-to-a-random-secret-key"
    database_url: str = "sqlite:///./meeting_notetaker.db"
    llm_endpoint: str = "http://localhost:11434/v1"
    llm_model: str = "llama3.2"
    llm_api_key: str = "not-needed"
    whisper_model: str = "base"
    audio_dir: str = "./audio_recordings"
    bot_headless: bool = False
    bot_timeout_minutes: int = 120

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
