import os
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hypothesis Generation System"
    API_KEY: str = os.getenv("YANDEX_API_KEY", "")
    FOLDER_ID: str = os.getenv("YANDEX_FOLDER_ID", "")
    LLM_API_BASE: str = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
    CHROMA_DB_DIR: str = "./chroma_db"
    
    class Config:
        env_file = ".env"

settings = Settings()
