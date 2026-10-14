import logging
import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.afisha.afisha import Afisha, AfishaUpdate
from src.usecase.afisha.dto.afisha import AfishaDetailResult, AfishaListResult
from src.usecase.port.afisha.afisha_repositories import AfishaRepository

logger = logging.getLogger(__name__)


class AfishaService:
    def __init__(self, repo: AfishaRepository | None = None) -> None:
        self.repo = repo

    @staticmethod
    def _stub_detail(afisha: Afisha) -> AfishaDetailResult:
        return AfishaDetailResult(
            afisha=afisha,
            reviews_id=uuid.uuid4(),
            average_id=uuid.uuid4(),
            created_at=afisha.created_at,
            updated_at=afisha.updated_at,
        )

    async def create_afisha(
        self,
        afisha: Afisha,
        session: AsyncSession,
        images: list[UploadFile] | None,
    ) -> AfishaDetailResult:
        return self._stub_detail(afisha)

    async def update_afisha(
        self,
        afisha: Afisha,
        afisha_id: uuid.UUID,
        session: AsyncSession,
    ) -> AfishaDetailResult:
        afisha.id = afisha_id
        return self._stub_detail(afisha)

    async def patch_afisha(
        self,
        afisha: AfishaUpdate,
        afisha_id: uuid.UUID,
        session: AsyncSession,
    ) -> AfishaDetailResult:
        raise NotImplementedError("Обновление афиши ещё не реализовано")

    async def delete_afisha(
        self,
        afisha_id: uuid.UUID,
        session: AsyncSession,
    )-> None:
        return

    async def list_afisha(
        self,
        session: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> AfishaListResult:
        return AfishaListResult(items=[], total=0, page=page, page_size=page_size)

    async def read_afisha(
        self,
        afisha_id: uuid.UUID,
        session: AsyncSession,
    ) -> AfishaDetailResult:
        raise NotImplementedError("Чтение афиши ещё не реализовано")


afisha_service = AfishaService()
