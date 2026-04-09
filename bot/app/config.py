from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str = "your:bot_token"
    backend_internal_url: str = "http://backend:8000"
    bot_internal_secret: str = "dev-bot-secret"
    database_url_sync: str = "postgresql://campus_user:campus_pass@db:5432/campus_resource"
    tz: str = "Europe/Moscow"


settings = Settings()
