from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.storage.postgres.db_helper import db_helper
from src.transport.api.v1.map.auth.user import map_to_auth_response
from src.transport.api.v1.middleware.auth_cookie import (
    REFRESH_COOKIE_NAME,
    clear_refresh_cookie,
    prevent_caching,
    require_csrf_header,
    set_refresh_cookie,
)
from src.transport.api.v1.middleware.user_check import CurrentUserDep
from src.transport.api.v1.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from src.usecase.auth.auth_service import (
    InvalidCredentialsError,
    InvalidTokenError,
    UsernameAlreadyExistsError,
    auth_service,
)

router = APIRouter(prefix="/auth", tags=["Auth"])
SessionDep = Annotated[AsyncSession, Depends(db_helper.get_session)]
RefreshCookie = Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)]


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf_header)],
)
async def register(
    data: RegisterRequest,
    response: Response,
    session: SessionDep,
) -> AuthResponse:
    try:
        result = await auth_service.create_user(data.username, data.password, session)
    except UsernameAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "USERNAME_ALREADY_EXISTS",
                    "message": "username already exists",
                }
            },
        ) from exc
    set_refresh_cookie(response, result)
    return map_to_auth_response(result)


@router.post("/login", dependencies=[Depends(require_csrf_header)])
async def login(
    data: LoginRequest, response: Response, session: SessionDep
) -> AuthResponse:
    try:
        result = await auth_service.login(data.username, data.password, session)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "invalid username or password",
                }
            },
            headers={"Cache-Control": "no-store"},
        ) from exc
    set_refresh_cookie(response, result)
    return map_to_auth_response(result)


@router.post(
    "/refresh", response_model=AuthResponse, dependencies=[Depends(require_csrf_header)]
)
async def refresh(
    response: Response, session: SessionDep, refresh_token: RefreshCookie = None
) -> AuthResponse | JSONResponse:
    try:
        if refresh_token is None:
            raise InvalidTokenError
        result = await auth_service.refresh(refresh_token, session)
    except InvalidTokenError:
        error = JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "detail": {
                    "error": {"code": "UNAUTHORIZED", "message": "invalid token"}
                }
            },
        )
        clear_refresh_cookie(error)
        return error
    set_refresh_cookie(response, result)
    return map_to_auth_response(result)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf_header)],
)
async def logout(session: SessionDep, refresh_token: RefreshCookie = None) -> Response:
    await auth_service.logout(refresh_token, session)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_refresh_cookie(response)
    return response


@router.get("/me")
async def me(current_user: CurrentUserDep, response: Response) -> UserResponse:
    prevent_caching(response)
    return UserResponse(
        id=current_user.user_id, username=current_user.username, role=current_user.role
    )
