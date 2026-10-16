from datetime import UTC, datetime
from typing import Annotated

from fastapi import Header, HTTPException, Request, Response, status

from src.core.config import settings
from src.usecase.auth.dto.auth import AuthResult

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/auth"


def require_csrf_header(
    request: Request,
    x_requested_with: Annotated[
        str | None,
        Header(
            description=(
                "Обязательный CSRF-заголовок: XMLHttpRequest. "
                "Swagger подставляет пример только в интерфейсе. "
                "Без заголовка или с другим значением сервер вернёт 403 CSRF_FAILED."
            ),
            openapi_examples={
                "csrf": {
                    "summary": "Заголовок для авторизации с cookie",
                    "value": "XMLHttpRequest",
                }
            },
        ),
    ] = None,
) -> None:
    origin = request.headers.get("origin")
    same_origin = str(request.base_url).rstrip("/")
    if x_requested_with != "XMLHttpRequest" or (
        origin is not None
        and origin != same_origin
        and origin not in settings.cors_origins
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "CSRF_FAILED",
                    "message": "request origin or header is invalid",
                }
            },
        )


def prevent_caching(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


def set_refresh_cookie(response: Response, result: AuthResult) -> None:
    prevent_caching(response)
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=result.refresh_token,
        max_age=max(
            0, int((result.refresh_expires_at - datetime.now(UTC)).total_seconds())
        ),
        expires=result.refresh_expires_at,
        path=REFRESH_COOKIE_PATH,
        secure=settings.auth_cookie_secure,
        httponly=True,
        samesite=settings.auth_cookie_samesite,
    )


def clear_refresh_cookie(response: Response) -> None:
    prevent_caching(response)
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        secure=settings.auth_cookie_secure,
        httponly=True,
        samesite=settings.auth_cookie_samesite,
    )
