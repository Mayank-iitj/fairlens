from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "FairLens API"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    docs_enabled: bool = True
    allowed_hosts: list[str] = Field(default_factory=lambda: ["*"])
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 10080

    database_url: str = "postgresql+psycopg2://fairlens:fairlens@localhost:5432/fairlens"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "fairlens"
    minio_secret_key: str = "fairlens-secret"
    minio_bucket: str = "datasets"
    minio_secure: bool = False
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-70b-versatile"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_client_ids: list[str] = Field(default_factory=list)
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "https://fairlens.mayyanks.app",
            "https://www.fairlens.mayyanks.app",
            "https://dev.fairlens.mayyanks.app",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
        ]
    )

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        """Enforce secure runtime configuration in production-like environments."""
        env = self.environment.lower().strip()
        if env in {"prod", "production", "staging"}:
            if self.secret_key.strip() in {"", "change-me", "change-this"}:
                raise ValueError("SECRET_KEY must be set to a strong non-default value in production/staging")
            if not self.groq_api_key.strip():
                raise ValueError("GROQ_API_KEY must be set in production/staging")
            if "*" in self.allowed_hosts:
                raise ValueError("ALLOWED_HOSTS must not contain '*' in production/staging")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()