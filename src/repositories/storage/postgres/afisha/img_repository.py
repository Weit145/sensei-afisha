import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.err import NotFoundError
from src.repositories.storage.models.afisha import AfishaImageModel


class SQLAlchemyImgRepository:
    async def create_img(
        self,
        session: AsyncSession,
        img: AfishaImageModel,
    ) -> None:
        session.add(img)

    async def list_img_by_afisha_id(
        self,
        session: AsyncSession,
        afisha_id: uuid.UUID,
    ) -> list[AfishaImageModel]:
        query = (
            select(AfishaImageModel)
            .where(AfishaImageModel.afisha_id == afisha_id)
            .order_by(AfishaImageModel.position, AfishaImageModel.id)
        )
        return list((await session.scalars(query)).all())

    async def img_by_afish_img_id(
        self,
        session: AsyncSession,
        afisha_id: uuid.UUID,
        image_id: uuid.UUID,
    ) -> AfishaImageModel | None:
        query =(
            select(AfishaImageModel)
            .where(
                AfishaImageModel.afisha_id == afisha_id,
                AfishaImageModel.id == image_id)
        )
        return await session.scalar(query)

    async def delete_img(
        self,
        session: AsyncSession,
        afisha_id: uuid.UUID,
        image_id: uuid.UUID,
    ) -> None:
        image = await self.img_by_afish_img_id(session, afisha_id, image_id)
        if image is None:
            raise NotFoundError("Изображение афиши не найдено")
        await session.delete(image)
        await session.flush()

    async def set_cover(
        self,
        session: AsyncSession,
        afisha_id: uuid.UUID,
        image_id: uuid.UUID,
    ) -> None:
        query = (
            select(AfishaImageModel)
            .where(AfishaImageModel.afisha_id == afisha_id)
            .with_for_update()
        )
        images = (await session.scalars(query)).all()
        if not any(image.id == image_id for image in images):
            raise NotFoundError("Изображение афиши не найдено")

        for image in images:
            image.is_cover = image.id == image_id
        await session.flush()
