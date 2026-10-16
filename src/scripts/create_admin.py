import asyncio
import secrets

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.domain.user import UserRole
from src.infrastructure.password import hash_password
from src.repositories.storage.models import UserModel
from src.repositories.storage.postgres.db_helper import db_helper


async def create_admin(session: AsyncSession, password: str | None) -> bool:
    async with session.begin():
        query = select(UserModel.role).where(UserModel.username == "admin")
        role = await session.scalar(query)
        created = False
        if role is None:
            if (
                password is None
                or not 8 <= len(password) <= 128
                or not password.strip()
            ):
                raise ValueError(
                    "Set ADMIN_PASSWORD in .env: 8–128 characters, not blank"
                )
            user_id = await session.scalar(
                insert(UserModel)
                .values(
                    username="admin",
                    role=UserRole.ADMIN.value,
                    hashed_password=hash_password(password),
                )
                .on_conflict_do_nothing(index_elements=[UserModel.username])
                .returning(UserModel.id)
            )
            created = user_id is not None
            role = await session.scalar(query)
        if role != UserRole.ADMIN:
            raise ValueError("Username 'admin' is already taken by a non-admin account")
        return created


async def main() -> None:
    try:
        configured_password = (
            settings.admin_password.get_secret_value()
            if settings.admin_password is not None
            else None
        )
        generated_password = None
        if configured_password is None or not configured_password.strip():
            generated_password = secrets.token_urlsafe(32)
        password = generated_password or configured_password
        async with db_helper.session_factory() as session:
            created = await create_admin(session, password)
        print("Admin account created" if created else "Admin account already exists")
        if created and generated_password is not None:
            print(
                "Generated ADMIN_PASSWORD for admin (save it now): "
                f"{generated_password}"
            )
    finally:
        await db_helper.engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
