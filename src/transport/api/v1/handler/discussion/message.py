import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.err import DomainError
from src.repositories.storage.postgres.db_helper import db_helper
from src.repositories.storage.postgres.message_repository import (
    SQLAlchemyMessageRepository,
)
from src.transport.api.v1.map.discussion.message import (
    map_to_domain,
    map_to_list_response,
    map_to_response,
)
from src.transport.api.v1.map.err import map_error_to_http_status_code
from src.transport.api.v1.middleware.user_check import CurrentUserDep
from src.transport.api.v1.schemas.discussion.message import (
    CreateMessage,
    MessageListResponse,
    MessageResponse,
)
from src.usecase.discussion.message_service import MessageService

router = APIRouter(prefix="/afisha/{afisha_id}/messages", tags=["Discussion"])
message_service = MessageService(SQLAlchemyMessageRepository())
SessionDep = Annotated[AsyncSession, Depends(db_helper.get_session)]


@router.get(
    "",
    response_model=MessageListResponse,
    responses={404: {"description": "Concert not found"}},
)
async def list_messages(
    afisha_id: uuid.UUID, session: SessionDep
) -> MessageListResponse:
    try:
        result = await message_service.list_messages(afisha_id, session)
    except DomainError as error:
        map_error_to_http_status_code(error)
    return map_to_list_response(result)


@router.post(
    "",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Invalid authorization or token user does not exist"},
        404: {"description": "Concert not found"},
    },
)
async def create_message(
    afisha_id: uuid.UUID,
    data: CreateMessage,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> MessageResponse:
    try:
        result = await message_service.create_message(
            map_to_domain(data, afisha_id, current_user.user_id), session
        )
    except DomainError as error:
        map_error_to_http_status_code(error)
    return map_to_response(result)
