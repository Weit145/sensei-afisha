import uuid

from sqlalchemy.ext.asyncio import AsyncSession

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
        afisha_id:uuid.UUID,
    )->list[AfishaImageModel]:
        ...

    async def img_by_afish_img_id(
        self,
        session: AsyncSession,
        afisha_id: uuid.UUID,
        image_id: uuid.UUID,
    )->AfishaImageModel|None:
        ...

    async def delete_img(
        self,
        session: AsyncSession,
        afisha_id: uuid.UUID,
        image_id: uuid.UUID,
    ) -> None:
        ...

    async def set_cover(
        self,
        session: AsyncSession,
        afisha_id: uuid.UUID,
        image_id: uuid.UUID,
    ) -> None:
        ...
