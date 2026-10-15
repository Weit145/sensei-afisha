import logging
import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.afisha import Afisha, AfishaUpdate
from src.infrastructure.img import ImgInfastructure as ImgInfastructureMain
from src.repositories.storage.map.afisha import (
    map_afisha_to_domain as map_to_domain,
)
from src.repositories.storage.map.afisha import (
    map_afisha_to_list_item as map_to_list_item,
)
from src.repositories.storage.map.afisha import (
    map_afisha_to_model as map_to_model,
)
from src.repositories.storage.map.afisha import (
    map_file_names_to_models,
    map_to_image_item,
)
from src.repositories.storage.postgres.afisha import (
    SQLAlchemyAfishaRepository,
    SQLAlchemyImgRepository,
)
from src.usecase.afisha.dto import AfishaDetailResult, AfishaListResult
from src.usecase.port.afisha import AfishaRepository, ImgInfastructure, ImgRepository

logger = logging.getLogger(__name__)


class AfishaService:
    def __init__(
        self,
        afish_repo: AfishaRepository,
        img_repo: ImgRepository,
        img_inf: ImgInfastructure,
    ) -> None:
        self.afish_repo = afish_repo
        self.img_repo = img_repo
        self.img_inf = img_inf

    async def create_afisha(
        self,
        afisha: Afisha,
        session: AsyncSession,
        images: list[UploadFile] | None,
    ) -> AfishaDetailResult:
        db_afisha = map_to_model(afisha)
        file_names: list[str] = []
        try:
            await self.afish_repo.create_afisha(session, db_afisha, afisha.venue_ids)
            file_names = await self.img_inf.save_images(images or [])
            db_images = map_file_names_to_models(afisha.id, file_names)
            for db_image in db_images:
                await self.img_repo.create_img(session, db_image)
            result = self._stub_detail(afisha)
            result.images = [
                map_to_image_item(db_image)
                for db_image in db_images
            ]
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            for file_name in file_names:
                try:
                    await self.img_inf.delete_image(file_name)
                except Exception:
                    logger.exception("Не удалось удалить изображение %s", file_name)
            raise

    async def update_afisha(
        self,
        afisha: Afisha,
        afisha_id: uuid.UUID,
        session: AsyncSession,
    ) -> AfishaDetailResult:
        db_afisha = map_to_model(afisha)
        db_afisha.id = afisha_id
        try:
            db_result = await self.afish_repo.update_afisha(session, db_afisha, afisha_id)
            db_images = await self.img_repo.list_img_by_afisha_id(session, afisha_id)
            result = self._stub_detail(map_to_domain(db_result))
            result.images = [
                map_to_image_item(db_image)
                for db_image in sorted(db_images, key=lambda image: image.position)
            ]
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            raise

    async def patch_afisha(
        self,
        afisha: AfishaUpdate,
        afisha_id: uuid.UUID,
        session: AsyncSession,
    ) -> AfishaDetailResult:
        try:
            db_result = await self.afish_repo.patch_afisha(session, afisha_id, afisha)
            db_images = await self.img_repo.list_img_by_afisha_id(session, afisha_id)
            result = self._stub_detail(map_to_domain(db_result))
            result.images = [
                map_to_image_item(db_image)
                for db_image in sorted(db_images, key=lambda image: image.position)
            ]
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            raise

    async def delete_afisha(
        self,
        afisha_id: uuid.UUID,
        session: AsyncSession,
    ) -> None:
        try:
            db_images = await self.img_repo.list_img_by_afisha_id(session, afisha_id)
            await self.afish_repo.delete_afisha(session, afisha_id)
            await session.commit()
        except Exception:
            await session.rollback()
            raise

        for db_image in db_images:
            try:
                await self.img_inf.delete_image(db_image.file_name)
            except Exception:
                logger.exception("Не удалось удалить изображение %s", db_image.file_name)

    async def list_afisha(
        self,
        session: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> AfishaListResult:
        db_afishas, total = await self.afish_repo.list_afisha(
            session, page, page_size, search
        )
        return AfishaListResult(
            items=[map_to_list_item(db_afisha) for db_afisha in db_afishas],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def read_afisha(
        self,
        afisha_id: uuid.UUID,
        session: AsyncSession,
    ) -> AfishaDetailResult:
        db_afisha = await self.afish_repo.read_afisha(session, afisha_id)
        db_images = await self.img_repo.list_img_by_afisha_id(session, afisha_id)
        result = self._stub_detail(map_to_domain(db_afisha))
        result.images = [
            map_to_image_item(db_image)
            for db_image in sorted(db_images, key=lambda image: image.position)
        ]
        return result


    @staticmethod
    def _stub_detail(afisha: Afisha) -> AfishaDetailResult:
        return AfishaDetailResult(
            afisha=afisha,
            reviews_id=uuid.uuid4(), # Заглушка пока нет id
            created_at=afisha.created_at,
            updated_at=afisha.updated_at,
        )


afisha_service = AfishaService(
    afish_repo=SQLAlchemyAfishaRepository(),
    img_repo=SQLAlchemyImgRepository(),
    img_inf=ImgInfastructureMain(),
)
