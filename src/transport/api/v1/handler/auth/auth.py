from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.storage.postgres.db_helper import db_helper
from src.transport.api.v1.map.auth.user import map_to_response
from src.transport.api.v1.schemas.auth import RegisterRequest, UserResponse
from src.usecase.auth.auth_service import UsernameAlreadyExistsError, auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
) -> UserResponse:
    try:
        user = await auth_service.create_user(data.username, data.password, session)
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
    return map_to_response(user)
