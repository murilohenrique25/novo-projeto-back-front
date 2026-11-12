from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/delivery"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Admin credentials (seeded on startup)
    admin_email: str = "admin@delivery.com"
    admin_password: str = "admin123"

    # App
    app_name: str = "Delivery Management System"
    debug: bool = False


settings = Settings()
