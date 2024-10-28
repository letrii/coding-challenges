import os
from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Quiz Service"
    DEBUG: bool = False
    QUIZ_SERVICE_PORT: str = "8000"
    DOCKER_NETWORK_NAME: str = "quiz_network"

    MONGODB_USERNAME: str = os.getenv("MONGODB_USERNAME", "admin")
    MONGODB_PASSWORD: str = os.getenv("MONGODB_PASSWORD", "password")
    MONGODB_HOST: str = os.getenv("MONGODB_HOST", "mongodb")
    MONGODB_PORT: str = os.getenv("MONGODB_PORT", "27017")
    MONGODB_DB: str = os.getenv("MONGODB_DB", "quiz_db")
    MONGODB_URL: str = ""

    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: str = os.getenv("REDIS_PORT", "6379")
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379")

    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

    @property
    def get_mongodb_url(self) -> str:
        username = quote_plus(self.MONGODB_USERNAME)
        password = quote_plus(self.MONGODB_PASSWORD)
        return (
            f"mongodb://{username}:{password}@"
            f"{self.MONGODB_HOST}:{self.MONGODB_PORT}/"
            f"{self.MONGODB_DB}?authSource=admin"
        )


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.MONGODB_URL = settings.get_mongodb_url
    return settings
