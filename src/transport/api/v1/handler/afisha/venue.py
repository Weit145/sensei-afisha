import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Path,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.err import DomainError
from src.repositories.storage.postgres.db_helper import db_helper
from src.transport.api.v1.map.afisha import (
    map_venue_to_domain as map_to_domain,
)
from src.transport.api.v1.map.afisha import (
    map_venue_to_list_response as map_to_list_response,
)
from src.transport.api.v1.map.afisha import (
    map_venue_to_response as map_to_response,
)
from src.transport.api.v1.map.afisha import (
    map_venue_to_update_domain as map_to_update_domain,
)
from src.transport.api.v1.map.err import map_error_to_http_status_code
from src.transport.api.v1.middleware.user_check import CurrentUser, require_admin
from src.transport.api.v1.schemas.afisha import (
    CreateVenue,
    ResponseVenue,
    UpdateVenue,
    VenueListResponse,
)
from src.usecase.afisha.venue_service import venue_service

router = APIRouter(prefix="/venues", tags=["Venue"])


@router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    description="Создаёт площадку для проведения мероприятий.",
)
async def create_venue(
    venue: CreateVenue,
    # _:Annotated[CurrentUser, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->ResponseVenue:
    try:
        domain_venue = map_to_domain(venue)
        result = await venue_service.create_venue(domain_venue,session)
    except DomainError as error:
        map_error_to_http_status_code(error)
    return map_to_response(result)


@router.put(
    path="/{venue_id}",
    status_code=status.HTTP_200_OK,
    description="Полностью обновляет данные площадки.",
)
async def update_venue(
    venue:CreateVenue,
    # _:Annotated[CurrentUser, Depends(require_admin)],
    venue_id: Annotated[uuid.UUID, Path(title="The ID venue")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->ResponseVenue:
    try:
            domain_venue = map_to_domain(venue)
            result = await venue_service.update_venue(domain_venue,venue_id,session)
    except DomainError as error:
        map_error_to_http_status_code(error)
    return map_to_response(result)

@router.patch(
    path="/{venue_id}",
    status_code=status.HTTP_200_OK,
    description="Частично обновляет указанные поля площадки.",
)
async def patch_venue(
    venue:UpdateVenue,
    # _:Annotated[CurrentUser, Depends(require_admin)],
    venue_id: Annotated[uuid.UUID, Path(title="The ID venue")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->ResponseVenue:
    try:
        domain_updaye_venue = map_to_update_domain(venue)
        result = await venue_service.patch_venue(domain_updaye_venue,venue_id,session)
    except DomainError as error:
        map_error_to_http_status_code(error)
    return map_to_response(result)

@router.delete(
    path="/{venue_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Удаляет площадку по её идентификатору.",
)
async def delete_venue(
    # _:Annotated[CurrentUser, Depends(require_admin)],
    venue_id: Annotated[uuid.UUID, Path(title="The ID venue")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->None:
    try:
        await venue_service.delete_venue(venue_id, session)
    except DomainError as error:
        map_error_to_http_status_code(error)


@router.get(
    path="",
    status_code=status.HTTP_200_OK,
    description="Возвращает список площадок с поиском и постраничной навигацией.",
)
async def list_venues(
    session: Annotated[AsyncSession,Depends(db_helper.get_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: str | None = None,
) -> VenueListResponse:
    try:
        result = await venue_service.list_venue(session, page, page_size, search)
    except DomainError as error:
        map_error_to_http_status_code(error)
    return map_to_list_response(result)


@router.get(
    path="/{venue_id}",
    status_code=status.HTTP_200_OK,
    description="Возвращает подробные данные площадки по её идентификатору.",
)
async def read_venue(
    venue_id: Annotated[uuid.UUID, Path(title="The ID venue")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->ResponseVenue:
    try:
        result = await venue_service.read_venue(venue_id, session)
    except DomainError as error:
        map_error_to_http_status_code(error)
    return map_to_response(result)
