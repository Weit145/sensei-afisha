import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Path,
    Query,
    Request,
    UploadFile,
    status,
)
from pydantic import Json
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from src.repositories.storage.postgres.db_helper import db_helper
from src.transport.api.v1.handler.afisha.image_storage import save_image
from src.transport.api.v1.schemas.afisha.afisha import (
    AfishaListResponse,
    CreateAfisha,
    ResponseAfisha,
    UploadedImageResponse,
    UpdateAfisha,
)

router = APIRouter(prefix="/afisha", tags=["Afisha"])

def check_role():
    pass

class Admin:
    id

class User:
    id

@router.post("/images", status_code=status.HTTP_201_CREATED)
async def upload_afisha_image(
    request: Request,
    image: Annotated[UploadFile, File()],
    admin: Annotated[Admin, Depends(check_role)],
) -> UploadedImageResponse:
    image_id, filename = await run_in_threadpool(save_image, image)
    return UploadedImageResponse(
        id=image_id,
        image_url=str(request.url_for("uploads", path=filename)),
    )

@router.post(path="",status_code=status.HTTP_201_CREATED)
async def create_afisha(
    afisha: Annotated[Json[CreateAfisha], Form()],
    admin:Annotated[Admin, Depends(check_role)],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
    images: Annotated[list[UploadFile] | None, File()] = None,
)->ResponseAfisha:
    return ResponseAfisha()

@router.put(path="/{afisha_id}",status_code=status.HTTP_200_OK)
async def update_afisha(
    afisha:CreateAfisha,
    admin:Annotated[Admin, Depends(check_role)],
    afisha_id: Annotated[uuid.UUID, Path(title="The ID afisha")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->ResponseAfisha:
    return ResponseAfisha()

@router.patch(path="/{afisha_id}",status_code=status.HTTP_200_OK)
async def patch_afisha(
    afisha:UpdateAfisha,
    admin:Annotated[Admin, Depends(check_role)],
    afisha_id: Annotated[uuid.UUID, Path(title="The ID afisha")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->ResponseAfisha:
    return ResponseAfisha()

@router.delete(path="/{afisha_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_afisha(
    admin:Annotated[Admin, Depends(check_role)],
    afisha_id: Annotated[uuid.UUID, Path(title="The ID afisha")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->None:
    return


@router.get(path="",  status_code=status.HTTP_200_OK)
async def list_afisha(
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: str | None = None,
)->AfishaListResponse:
    return []

@router.get(path="/{afisha_id}",status_code=status.HTTP_200_OK)
async def read_afisha(
    afisha_id: Annotated[uuid.UUID, Path(title="The ID afisha")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->ResponseAfisha:
    return ResponseAfisha()
