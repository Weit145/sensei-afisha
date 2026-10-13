from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.storage.postgres.db_helper import db_helper
from src.transport.api.v1.map.user import map_to_domain, map_to_response
from src.transport.api.v1.schemas.user import CreateUser, UserResponse
from src.usecase.service import service

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: CreateUser,
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
) -> UserResponse:
    user = await service.create_user(map_to_domain(data), session)
    return map_to_response(user)
