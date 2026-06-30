from functools import lru_cache
from typing import ClassVar
from urllib.parse import unquote
from urllib.parse import urlparse

from pydantic import AnyUrl, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_SECRET_KEY = "change-this-secret-key"
DEFAULT_POSTGRES_PASSWORD = "vyaparsetu"
MIN_DATABASE_PASSWORD_LENGTH = 12
PLACEHOLDER_VALUES = {
    "",
    "change-this-whatsapp-verify-token",
    "change-this-secret-key",
    "replace-with-a-long-random-secret",
    "replace-with-64-char-random-secret",
    "replace-with-strong-password",
    "replace_with_strong_password",
    "replace_with_64_char_random_secret",
    "replace_with_openai_api_key",
    "replace_with_production_ai_provider",
}
LOCALHOST_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
PRODUCTION_ENVIRONMENTS = {"production", "prod", "live"}
NON_PRODUCTION_ENVIRONMENTS = {"development", "dev", "local", "test", "testing", "staging"}


class Settings(BaseSettings):
    PRODUCTION_READY_AI_PROVIDERS: ClassVar[set[str]] = set()

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

    SECRET_KEY: str = Field(default=DEFAULT_SECRET_KEY)
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "vyaparsetu-api"
    JWT_AUDIENCE: str = "vyaparsetu-web"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    BACKEND_CORS_ORIGINS: list[AnyUrl] = []
    NEXT_PUBLIC_API_BASE_URL: AnyUrl | None = None

    FIRST_ADMIN_EMAIL: str | None = None
    FIRST_ADMIN_PASSWORD: str | None = None
    FIRST_ADMIN_FULL_NAME: str | None = "VyaparSetu Admin"

    UPLOAD_DIR: str = "storage/uploads"
    MAX_UPLOAD_FILE_SIZE_BYTES: int = 10 * 1024 * 1024
    AI_PROVIDER: str = "mock"
    DOCUMENT_INTELLIGENCE_ENABLED: bool = True
    OPENAI_API_KEY: str | None = None
    NOTIFICATION_PROVIDER: str = "mock"
    WHATSAPP_PROVIDER: str = "mock"
    WHATSAPP_VERIFY_TOKEN: str = "change-this-whatsapp-verify-token"
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

    def normalized_environment(self) -> str:
        return self.ENVIRONMENT.strip().lower()

    def is_production_environment(self) -> bool:
        return self.normalized_environment() in PRODUCTION_ENVIRONMENTS

    @staticmethod
    def is_placeholder(value: str) -> bool:
        normalized_value = value.strip().lower()
        return (
            normalized_value in PLACEHOLDER_VALUES
            or normalized_value.startswith(("replace-with", "replace_with"))
        )

    @classmethod
    def validate_database_password(cls, password: str, source: str, errors: list[str]) -> None:
        if (
            cls.is_placeholder(password)
            or password == DEFAULT_POSTGRES_PASSWORD
            or len(password) < MIN_DATABASE_PASSWORD_LENGTH
        ):
            errors.append(
                f"{source} must use a non-default database password of at least "
                f"{MIN_DATABASE_PASSWORD_LENGTH} characters"
            )

    def validate_environment_name(self) -> None:
        environment = self.normalized_environment()
        if environment in PRODUCTION_ENVIRONMENTS or environment in NON_PRODUCTION_ENVIRONMENTS:
            return
        allowed_values = sorted(PRODUCTION_ENVIRONMENTS | NON_PRODUCTION_ENVIRONMENTS)
        raise RuntimeError(
            "Unrecognized ENVIRONMENT value. "
            f"Use one of: {', '.join(allowed_values)}"
        )

    def validate_production_safety(self) -> None:
        self.validate_environment_name()
        if not self.is_production_environment():
            return

        errors: list[str] = []

        secret_key = self.SECRET_KEY.strip()
        postgres_password = self.POSTGRES_PASSWORD.strip()

        normalized_secret_key = secret_key.lower()

        if (
            normalized_secret_key in PLACEHOLDER_VALUES
            or normalized_secret_key.startswith(("replace-with", "replace_with"))
            or len(secret_key) < 32
        ):
            errors.append("SECRET_KEY must be a non-default random value of at least 32 characters")
        self.validate_database_password(postgres_password, "POSTGRES_PASSWORD", errors)
        if self.DATABASE_URL is None:
            errors.append("DATABASE_URL is required in production")
        else:
            database_password = unquote(urlparse(str(self.DATABASE_URL)).password or "")
            if not database_password:
                errors.append("DATABASE_URL must include a database password in production")
            else:
                self.validate_database_password(
                    database_password,
                    "DATABASE_URL password",
                    errors,
                )
        if self.DOCUMENT_INTELLIGENCE_ENABLED:
            if self.AI_PROVIDER.lower() == "mock":
                errors.append("AI_PROVIDER=mock is not allowed in production when document intelligence is enabled")
            elif self.AI_PROVIDER.lower() not in self.PRODUCTION_READY_AI_PROVIDERS:
                errors.append(
                    f"AI_PROVIDER={self.AI_PROVIDER} is not production-ready or implemented. "
                    "Disable DOCUMENT_INTELLIGENCE_ENABLED or configure a production-ready provider."
                )
        whatsapp_provider = self.WHATSAPP_PROVIDER.strip().lower()
        if whatsapp_provider != "mock":
            whatsapp_verify_token = self.WHATSAPP_VERIFY_TOKEN.strip()
            if not whatsapp_provider:
                errors.append("WHATSAPP_PROVIDER is required when WhatsApp is enabled")
            elif whatsapp_provider not in {"meta", "cloud_api", "twilio", "360dialog"}:
                errors.append(f"Unsupported WHATSAPP_PROVIDER: {self.WHATSAPP_PROVIDER}")
            else:
                errors.append(
                    f"WHATSAPP_PROVIDER={self.WHATSAPP_PROVIDER} is configured but not integrated yet"
                )
            if self.is_placeholder(whatsapp_verify_token) or len(whatsapp_verify_token) < 16:
                errors.append(
                    "WHATSAPP_VERIFY_TOKEN must be a non-placeholder value of at least "
                    "16 characters when WhatsApp is enabled"
                )
        if not self.BACKEND_CORS_ORIGINS:
            errors.append("BACKEND_CORS_ORIGINS must contain the production HTTPS origin")
        if self.NEXT_PUBLIC_API_BASE_URL is None:
            errors.append("NEXT_PUBLIC_API_BASE_URL is required in production")
        if self.ADMIN_NOTIFICATION_EMAIL is None:
            errors.append("ADMIN_NOTIFICATION_EMAIL is required in production")
        if self.DOCUMENT_INTELLIGENCE_ENABLED and self.AI_PROVIDER.lower() == "openai" and (
            not self.OPENAI_API_KEY
            or self.OPENAI_API_KEY.lower().startswith(("replace-with", "replace_with"))
        ):
            errors.append("OPENAI_API_KEY is required when AI_PROVIDER=openai")

        for origin in self.BACKEND_CORS_ORIGINS:
            parsed_origin = urlparse(str(origin))
            if parsed_origin.scheme != "https":
                errors.append(f"BACKEND_CORS_ORIGINS must use https: {origin}")
            if parsed_origin.hostname in LOCALHOST_HOSTS:
                errors.append(f"BACKEND_CORS_ORIGINS cannot include localhost origins: {origin}")

        if self.NEXT_PUBLIC_API_BASE_URL is not None:
            parsed_api_url = urlparse(str(self.NEXT_PUBLIC_API_BASE_URL))
            if parsed_api_url.scheme != "https":
                errors.append("NEXT_PUBLIC_API_BASE_URL must use https in production")
            if parsed_api_url.hostname in LOCALHOST_HOSTS:
                errors.append("NEXT_PUBLIC_API_BASE_URL cannot point to localhost in production")

        if errors:
            joined_errors = "; ".join(errors)
            raise RuntimeError(f"Unsafe production configuration: {joined_errors}")


@lru_cache
def get_settings() -> Settings:
    loaded_settings = Settings()
    loaded_settings.validate_production_safety()
    return loaded_settings


settings = get_settings()
