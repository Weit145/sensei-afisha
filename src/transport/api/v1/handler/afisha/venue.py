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
from src.transport.api.v1.schemas.afisha.venue import (
    CreateVenue,
    ResponseVenue,
    UpdateVenue,
    VenueListResponse,
)

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
    admin:Annotated[Admin, Depends(check_role)],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->ResponseVenue:
    return ResponseVenue()


@router.put(path="/{venue_id}",status_code=status.HTTP_200_OK)
async def update_afisha(
    venue:CreateVenue,
    admin:Annotated[Admin, Depends(check_role)],
    venue_id: Annotated[uuid.UUID, Path(title="The ID venue")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->ResponseVenue:
    return ResponseVenue()

@router.patch(path="/{venue_id}",status_code=status.HTTP_200_OK)
async def patch_afisha(
    afisha:UpdateVenue,
    admin:Annotated[Admin, Depends(check_role)],
    venue_id: Annotated[uuid.UUID, Path(title="The ID venue")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->ResponseVenue:
    return ResponseVenue()

@router.delete(path="/{venue_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_afisha(
    admin:Annotated[Admin, Depends(check_role)],
    venue_id: Annotated[uuid.UUID, Path(title="The ID venue")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->None:
    return


@router.get(path="",status_code=status.HTTP_200_OK)
async def list_venues(
    session: Annotated[AsyncSession,Depends(db_helper.get_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: str | None = None,
) -> VenueListResponse:
    return VenueListResponse()

@router.get(path="/{venue_id}",status_code=status.HTTP_200_OK)
async def read_afisha(
    venue_id: Annotated[uuid.UUID, Path(title="The ID venue")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->ResponseVenue:
    return ResponseVenue()
