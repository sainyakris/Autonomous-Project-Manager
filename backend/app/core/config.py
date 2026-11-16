from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # extra="ignore": unknown variables in .env won't crash startup
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "AutonomousPM"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str            # no default: the app refuses to start without it
    DATABASE_URL: str          # no default, same reason
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    FRONTEND_URL: str = "http://localhost:3000"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    @field_validator("DATABASE_URL")
    @classmethod
    def use_asyncpg_driver(cls, v: str) -> str:
        # Hosts hand out postgres:// or postgresql:// URLs, but our async
        # engine needs the +asyncpg driver in the scheme.
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
