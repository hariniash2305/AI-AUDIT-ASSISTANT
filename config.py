# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./audit.db"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()