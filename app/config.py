from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "M-Motors API"
    environment: str = "development"
    database_url: str = "sqlite:///./m_motors.db"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173"
    alert_webhook_url: str | None = None
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 5
    rate_limit_login: str = "5/minute"


settings = Settings()
