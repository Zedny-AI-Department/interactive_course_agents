from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    ALIGNMENT_API_URL: str = Field(alias='ALIGNMENT_API_URL')
    TRANSCRIPTION_API_URL: str = Field(alias='TRANSCRIPTION_API_URL')
    OPENAI_API_KEY: str = Field(alias="OPENAI_API_KEY")
    TAVILY_API_KEY: str = Field(alias="TAVILY_API_KEY")


    model_config = SettingsConfigDict(env_file=".env")  

settings = Settings()
