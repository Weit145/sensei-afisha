from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.err import DomainError
from src.repositories.storage.postgres.db_helper import db_helper
from src.transport.api.v1.map.err import map_error_to_http_status_code
from src.transport.api.v1.middleware.auth_cookie import prevent_caching
from src.transport.api.v1.middleware.user_check import CurrentUserDep
from src.transport.api.v1.schemas.auth import UserPublicContactsResponse
from src.usecase.auth.auth_service import auth_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/{user_id}/contacts",
    response_model=UserPublicContactsResponse,
    description="Возвращает ник и указанные пользователем Telegram/VK для связи. Требуется вход в клуб.",
    responses={404: {"description": "Пользователь не найден"}},
)
async def get_user_contacts(
    user_id: UUID,
    _: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
    response: Response,
) -> UserPublicContactsResponse:
    try:
        user = await auth_service.get_user_contacts(user_id, session)
    except DomainError as error:
        map_error_to_http_status_code(error)
    prevent_caching(response)
    return UserPublicContactsResponse(
        user_id=user.id,
        nickname=user.username,
        tg_url=user.tg_url,
        vk_url=user.vk_url,
    )
