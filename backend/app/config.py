from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://campus_user:campus_pass@db:5432/campus_resource"
    database_url_sync: str = "postgresql://campus_user:campus_pass@db:5432/campus_resource"

    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    refresh_token_expire_days: int = 30

    bot_internal_secret: str = "dev-bot-secret"
    frontend_url: str = "http://localhost:5173"
    openrouter_api_key: str = ""
    ta_registration_code: str = "TA2026"
    admin_password: str = "admin123"


settings = Settings()
