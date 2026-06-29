from functools import lru_cache

from pydantic import AnyUrl, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "VyaparSetu"
    PROJECT_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "vyaparsetu"
    POSTGRES_PASSWORD: str = "vyaparsetu"
    POSTGRES_DB: str = "vyaparsetu"
    DATABASE_URL: PostgresDsn | None = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    SECRET_KEY: str = Field(default="change-this-secret-key")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    BACKEND_CORS_ORIGINS: list[AnyUrl] = []

    FIRST_ADMIN_EMAIL: str | None = None
    FIRST_ADMIN_PASSWORD: str | None = None
    FIRST_ADMIN_FULL_NAME: str | None = "VyaparSetu Admin"

    UPLOAD_DIR: str = "storage/uploads"
    MAX_UPLOAD_FILE_SIZE_BYTES: int = 10 * 1024 * 1024
    AI_PROVIDER: str = "mock"
    OPENAI_API_KEY: str | None = None
    NOTIFICATION_PROVIDER: str = "mock"
    ADMIN_NOTIFICATION_EMAIL: str | None = None
    PRICING_GST: str = "Contact us"
    PRICING_FSSAI: str = "Contact us"
    PRICING_UDYAM: str = "Contact us"
    RATE_LIMIT_PER_MINUTE: int = 120
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.DATABASE_URL is not None:
            return str(self.DATABASE_URL)
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
