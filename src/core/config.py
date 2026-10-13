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
    log_level: str = Field(
        "INFO",
        validation_alias="LOG_LEVEL",
    )
    upload_dir: str = Field("uploads", validation_alias="UPLOAD_DIR")


settings = Settings()  # pyright: ignore[reportCallIssue]  # Defaults are supplied by Field.
