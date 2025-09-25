from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    ALIGNMENT_API_URL: str = Field(alias="ALIGNMENT_API_URL")
    TRANSCRIPTION_API_URL: str = Field(alias="TRANSCRIPTION_API_URL")
    STORAGE_API_URL: str = Field(alias="STORAGE_API_URL")
    OPENAI_API_KEY: str = Field(alias="OPENAI_API_KEY")
    TAVILY_API_KEY: str = Field(alias="TAVILY_API_KEY")
    REDIS_URL: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    MAX_CONCURRENT_TASKS_PER_USER: int = Field(default=5, alias="MAX_CONCURRENT_TASKS_PER_USER")
    MAX_GLOBAL_CONCURRENT_TASKS: int = Field(default=20, alias="MAX_GLOBAL_CONCURRENT_TASKS")
    FAL_KEY: str = Field(alias="FAL_KEY")

    class Config:
        # Automatically read from .env file
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
