"""
IDKit Configuration Management

Uses Pydantic Settings for type-safe configuration with environment variable support.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True

    # API
    api_v1_prefix: str = "/api/v1"
    project_name: str = "IDKit"
    version: str = "0.1.0"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://idkit:idkit@localhost:5432/idkit",
        description="PostgreSQL connection URL",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # JWT Authentication
    jwt_secret_key: str = Field(
        default="your-super-secret-key-change-in-production",
        description="Secret key for JWT encoding",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    refresh_token_expire_days: int = 7

    # OAuth - Google
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    # OAuth - Apple
    apple_client_id: str = ""
    apple_team_id: str = ""
    apple_key_id: str = ""
    apple_private_key: str = ""

    # AI Providers
    openai_api_key: str = ""
    heygen_api_key: str = ""
    elevenlabs_api_key: str = ""

    # Storage - AWS S3 / MinIO
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket_name: str = "idkit-media"
    s3_endpoint_url: str | None = None  # Set for MinIO

    # Celery
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL",
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend URL",
    )

    # GPU Providers (for later)
    vastai_api_key: str = ""
    runpod_api_key: str = ""
    lambda_api_key: str = ""

    # Stripe
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""

    # Email - SendGrid
    sendgrid_api_key: str = ""

    # Email - Mailgun
    mailgun_api_key: str = ""
    mailgun_domain: str = ""

    # Email - SMTP (generic)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""

    # Email - Defaults
    default_from_email: str = "noreply@idkit.ai"
    default_from_name: str = "IDKit"

    # Frontend URL (for CORS)
    frontend_url: str = "http://localhost:3000"

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        """Allowed CORS origins."""
        origins = [self.frontend_url]
        if self.environment == "development":
            origins.extend([
                "http://localhost:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3000",
            ])
        return origins

    @computed_field
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience export
settings = get_settings()
