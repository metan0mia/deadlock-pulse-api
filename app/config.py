from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    secret_key: str = "dev-only-change-in-production"
    database_url: str = "sqlite+aiosqlite:///./pulse.db"
    deadlock_api_key: str = ""
    poll_interval_seconds: int = 45
    enable_poller: bool = True
    cors_origins: str = "*"
    access_token_expire_minutes: int = 60 * 24


settings = Settings()
