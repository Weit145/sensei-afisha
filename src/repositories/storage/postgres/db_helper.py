from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import settings


class DatabaseHelper:
    def __init__(self, url: str, echo: bool = False, **engine_kwargs: Any) -> None:
        self.engine = create_async_engine(url=url, echo=echo, **engine_kwargs)
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
        )

    async def get_session(self) -> AsyncGenerator[AsyncSession]:
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise


db_helper = DatabaseHelper(url=settings.database_url)
