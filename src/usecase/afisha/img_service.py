import logging
import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.usecase.port.afisha.img_repositories import ImgRepository

logger = logging.getLogger(__name__)


class ImgService:
    def __init__(self, repo: ImgRepository | None = None) -> None:
        self.repo = repo


    async def add_images(
        self,
        image: UploadFile,
        afisha_id: uuid.UUID,
        session: AsyncSession,
    ) -> None:
        return

    async def delete_image(
        self,
        image: UploadFile,
        afisha_id: uuid.UUID,
        image_id: uuid.UUID,
        session: AsyncSession,
    ) -> None:
        return

    async def change_main_img(
        self,
        afisha_id: uuid.UUID,
        image_id: uuid.UUID,
        session: AsyncSession,
    ) -> None:
        return

img_service = ImgService()
