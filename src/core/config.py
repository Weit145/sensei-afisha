from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    database_url: str = Field(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
        validation_alias="DATABASE_URL",
    )

    redis_url: str = Field(
        "redis://localhost:6379/0",
        validation_alias="REDIS_URL",
    )
    log_level: str = Field(
        "INFO",
        validation_alias="LOG_LEVEL",
    )
    upload_dir: str = Field("uploads", validation_alias="UPLOAD_DIR")

    jwt_secret_key: str = Field(validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(
        "HS256",
        validation_alias="JWT_ALGORITHM",
    )
    access_token_expire_minutes: int = Field(
        30,
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    mode: str = Field(
        "normal",
        validation_alias="MODE",
    )

settings = Settings()  # pyright: ignore[reportCallIssue]  # Defaults are supplied by Field.
