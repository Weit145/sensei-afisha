from typing import Literal

from pydantic import Field, model_validator
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

    jwt_secret_key: str = Field(min_length=32, validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(
        "HS256",
        validation_alias="JWT_ALGORITHM",
    )
    access_token_expire_minutes: int = Field(
        30,
        gt=0,
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    refresh_token_expire_days: int = Field(
        30, gt=0, validation_alias="REFRESH_TOKEN_EXPIRE_DAYS"
    )
    auth_cookie_secure: bool = Field(True, validation_alias="AUTH_COOKIE_SECURE")
    auth_cookie_samesite: Literal["lax", "strict", "none"] = Field(
        "lax", validation_alias="AUTH_COOKIE_SAMESITE"
    )
    cors_origins: list[str] = Field(
        default_factory=list, validation_alias="CORS_ORIGINS"
    )
    mode: str = Field(
        "normal",
        validation_alias="MODE",
    )

    @model_validator(mode="after")
    def validate_cookie_settings(self):
        if self.auth_cookie_samesite == "none" and not self.auth_cookie_secure:
            raise ValueError("SameSite=None requires AUTH_COOKIE_SECURE=true")
        if "*" in self.cors_origins:
            raise ValueError("CORS_ORIGINS must contain explicit origins")
        return self


settings = Settings()  # pyright: ignore[reportCallIssue]  # Defaults are supplied by Field.
