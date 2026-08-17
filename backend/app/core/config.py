from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://iarh:iarh@localhost:5432/iarh"
    cors_origins: str = "http://localhost:5173,http://localhost:8080,http://localhost:3000"
    ai_provider: str = "gemini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash"
    vertex_ai_enabled: bool = False
    google_cloud_project: str | None = None
    google_cloud_location: str = "us-central1"
    ai_credential_encryption_key: str | None = None
    payment_provider: str = "disabled"
    payment_currency: str = "USD"
    payment_webhook_secret: str | None = None
    payment_success_url: str = "http://localhost"
    payment_cancel_url: str = "http://localhost"
    redis_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"
    livekit_url: str = "ws://livekit:7880"
    livekit_public_url: str = "ws://localhost:7880"
    livekit_api_key: str | None = None
    livekit_api_secret: str | None = None
    livekit_token_ttl_seconds: int = 900
    media_s3_endpoint: str = "http://minio:9000"
    media_s3_public_endpoint: str | None = None
    media_s3_bucket: str = "iarh-media"
    media_s3_region: str = "us-east-1"
    media_s3_access_key: str | None = None
    media_s3_secret_key: str | None = None
    media_s3_presigned_ttl_seconds: int = 900
    transcription_provider: str = "faster-whisper"
    whisper_model: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    media_max_recording_bytes: int = 2_000_000_000
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 900
    refresh_token_ttl_seconds: int = 2592000
    interview_duration_minutes: int = 30
    rate_limit_enabled: bool = True
    email_verification_required: bool = False
    email_delivery_mode: str = "disabled"
    public_app_url: str = "http://localhost"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    email_from: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def validate_runtime_secrets(self) -> "Settings":
        if self.payment_provider != "disabled":
            raise ValueError("PAYMENT_PROVIDER is disabled until a verified provider adapter is installed")
        if len(self.payment_currency) != 3 or not self.payment_currency.isalpha():
            raise ValueError("PAYMENT_CURRENCY must be a three-letter currency code")
        if self.app_env.lower() in {"production", "prod"}:
            forbidden = {
                "CHANGE_ME_IN_PRODUCTION",
                "change-me",
                "iarh-livekit-dev-secret-change-me",
                "iarh-minio-secret-change-me",
            }
            secrets = {
                "JWT_SECRET_KEY": self.jwt_secret_key,
                "LIVEKIT_API_SECRET": self.livekit_api_secret,
                "MEDIA_S3_SECRET_KEY": self.media_s3_secret_key,
            }
            invalid = [name for name, value in secrets.items() if not value or value in forbidden]
            if invalid:
                raise ValueError(f"Production secrets are missing or use development defaults: {', '.join(invalid)}")
            if self.livekit_public_url.startswith("ws://"):
                raise ValueError("LIVEKIT_PUBLIC_URL must use wss:// in production")
            if self.media_s3_public_endpoint is None:
                raise ValueError("MEDIA_S3_PUBLIC_ENDPOINT is required in production")
            if not self.media_s3_public_endpoint.startswith("https://"):
                raise ValueError("MEDIA_S3_PUBLIC_ENDPOINT must use https:// in production")
            if "*" in self.cors_origins:
                raise ValueError("CORS_ORIGINS must not contain '*' in production")
            if self.vertex_ai_enabled and not self.google_cloud_project:
                raise ValueError("GOOGLE_CLOUD_PROJECT is required when Vertex AI is enabled")
            if not self.vertex_ai_enabled and not self.gemini_api_key:
                raise ValueError("GEMINI_API_KEY is required when Vertex AI is disabled")
            if not self.ai_credential_encryption_key:
                raise ValueError("AI_CREDENTIAL_ENCRYPTION_KEY is required in production")
            if self.payment_provider != "disabled" and not self.payment_webhook_secret:
                raise ValueError("PAYMENT_WEBHOOK_SECRET is required when payments are enabled")
            if self.email_verification_required:
                if self.email_delivery_mode != "smtp":
                    raise ValueError("SMTP email delivery is required when email verification is enabled")
                if not self.smtp_host or not self.email_from:
                    raise ValueError("SMTP_HOST and EMAIL_FROM are required in production")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
