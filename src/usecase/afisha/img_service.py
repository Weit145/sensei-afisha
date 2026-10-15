import logging
import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.err import NotFoundError
from src.infrastructure.img import ImgInfastructure as ImgInfastructureMain
from src.repositories.storage.map.afisha import (
    map_to_image_item,
    map_to_image_model,
)
from src.repositories.storage.postgres.afisha import SQLAlchemyImgRepository
from src.usecase.afisha.dto import AfishaImageItem
from src.usecase.port.afisha import ImgInfastructure, ImgRepository

logger = logging.getLogger(__name__)


class ImgService:
    def __init__(self, repo: ImgRepository, img_inf: ImgInfastructure) -> None:
        self.repo = repo
        self.img_inf = img_inf

    async def add_images(
        self,
        image: UploadFile,
        afisha_id: uuid.UUID,
        session: AsyncSession,
    ) -> AfishaImageItem:
        file_name: str | None = None
        try:
            existing_images = await self.repo.list_img_by_afisha_id(session, afisha_id)
            position = max((img.position for img in existing_images), default=-1) + 1
            is_cover = not any(img.is_cover for img in existing_images)

            file_name = await self.img_inf.save_image(image)
            db_image = map_to_image_model(afisha_id, file_name, position, is_cover)
            await self.repo.create_img(session, db_image)
            result = map_to_image_item(db_image)
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            if file_name is not None:
                try:
                    await self.img_inf.delete_image(file_name)
                except Exception:
                    logger.exception("Не удалось удалить изображение %s", file_name)
            raise

    async def delete_image(
        self,
        afisha_id: uuid.UUID,
        image_id: uuid.UUID,
        session: AsyncSession,
    ) -> None:
        try:
            db_image = await self.repo.img_by_afish_img_id(session, afisha_id,image_id)
            if db_image is None:
                raise NotFoundError("Изображение афиши не найдено")
            await self.repo.delete_img(session, afisha_id, image_id)
            if db_image.is_cover:
                db_images = await self.repo.list_img_by_afisha_id(session, afisha_id)

                next_cover = None

                for img in db_images:
                    if img.id == image_id:
                        continue
                    if next_cover is None or img.position < next_cover.position:
                        next_cover = img

                if next_cover is not None:
                    await self.repo.set_cover(session, afisha_id, next_cover.id)

            await session.commit()
        except Exception:
            await session.rollback()
            raise

        try:
            await self.img_inf.delete_image(db_image.file_name)
        except Exception:
            logger.exception("Не удалось удалить изображение %s", db_image.file_name)

    async def change_main_img(
        self,
        afisha_id: uuid.UUID,
        image_id: uuid.UUID,
        session: AsyncSession,
    ) -> None:
        try:
            await self.repo.set_cover(session, afisha_id, image_id)
            await session.commit()
        except Exception:
            await session.rollback()
            raise

img_service = ImgService(
    repo=SQLAlchemyImgRepository(),
    img_inf=ImgInfastructureMain(),
)
