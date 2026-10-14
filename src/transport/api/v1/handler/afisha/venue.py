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

from src.repositories.storage.postgres.db_helper import db_helper
from src.transport.api.v1.map.afisha.venue import (
    map_to_domain,
    map_to_list_response,
    map_to_response,
    map_to_update_domain,
)
from src.transport.api.v1.schemas.afisha.venue import (
    CreateVenue,
    ResponseVenue,
    UpdateVenue,
    VenueListResponse,
)
from src.usecase.afisha.venue_service import venue_service

router = APIRouter(prefix="/venues", tags=["Venue"])

def check_role():
    pass

class Admin:
    id: uuid.UUID

class User:
    id: uuid.UUID

@router.post(path="",status_code=status.HTTP_201_CREATED)
async def create_venue(
    venue: CreateVenue,
    _:Annotated[Admin, Depends(check_role)],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->ResponseVenue:
    domain_venue = map_to_domain(venue)
    result = await venue_service.create_venue(domain_venue,session)
    return map_to_response(result)


@router.put(path="/{venue_id}",status_code=status.HTTP_200_OK)
async def update_venue(
    venue:CreateVenue,
    _:Annotated[Admin, Depends(check_role)],
    venue_id: Annotated[uuid.UUID, Path(title="The ID venue")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->ResponseVenue:
    domain_venue = map_to_domain(venue)
    result = await venue_service.update_venue(domain_venue,venue_id,session)
    return map_to_response(result)

@router.patch(path="/{venue_id}",status_code=status.HTTP_200_OK)
async def patch_venue(
    venue:UpdateVenue,
    _:Annotated[Admin, Depends(check_role)],
    venue_id: Annotated[uuid.UUID, Path(title="The ID venue")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->ResponseVenue:
    domain_updaye_venue = map_to_update_domain(venue)
    result = await venue_service.patch_venue(domain_updaye_venue,venue_id,session)
    return map_to_response(result)

@router.delete(path="/{venue_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_venue(
    _:Annotated[Admin, Depends(check_role)],
    venue_id: Annotated[uuid.UUID, Path(title="The ID venue")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->None:
    return await venue_service.delete_venue(venue_id, session)


@router.get(path="",status_code=status.HTTP_200_OK)
async def list_venues(
    session: Annotated[AsyncSession,Depends(db_helper.get_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: str | None = None,
) -> VenueListResponse:
    result = await venue_service.list_venue(session,page,page_size)
    return map_to_list_response(result)


@router.get(path="/{venue_id}",status_code=status.HTTP_200_OK)
async def read_venue(
    venue_id: Annotated[uuid.UUID, Path(title="The ID venue")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->ResponseVenue:
    result = await venue_service.read_venue(venue_id, session)
    return map_to_response(result)
