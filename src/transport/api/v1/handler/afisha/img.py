import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Path,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.storage.postgres.db_helper import db_helper
from src.transport.api.v1.map.afisha import map_to_uploaded_image_response
from src.transport.api.v1.middleware.user_check import CurrentUser, require_admin
from src.transport.api.v1.schemas.afisha import UploadedImageResponse
from src.usecase.afisha.img_service import img_service

router = APIRouter(prefix="/afisha", tags=["Images"])

@router.post("/{afisha_id}/images", status_code=status.HTTP_201_CREATED)
async def add_images(
    image: Annotated[UploadFile, File()],
    afisha_id: Annotated[uuid.UUID, Path(title="The ID afisha")],
    _:Annotated[CurrentUser, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
) -> UploadedImageResponse:
    result = await img_service.add_images(image, afisha_id, session)
    return map_to_uploaded_image_response(result)

@router.delete("/{afisha_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    afisha_id: Annotated[uuid.UUID, Path(title="The ID afisha")],
    image_id: Annotated[uuid.UUID, Path(title="The ID image")],
    _:Annotated[CurrentUser, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->None:
    return await img_service.delete_image(afisha_id, image_id, session)

@router.patch("/{afisha_id}/images/{image_id}", status_code=status.HTTP_200_OK)
async def change_main_img(
    afisha_id: Annotated[uuid.UUID, Path(title="The ID afisha")],
    image_id: Annotated[uuid.UUID, Path(title="The ID image")],
    _:Annotated[CurrentUser, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->None:
    return await img_service.change_main_img(afisha_id,image_id,session)
