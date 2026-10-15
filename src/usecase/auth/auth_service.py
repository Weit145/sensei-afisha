from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.user import User, UserRole
from src.infrastructure.password import hash_password
from src.repositories.storage.map.user import map_to_domain, map_to_model
from src.repositories.storage.postgres.user_repository import SQLAlchemyUserRepository
from src.usecase.port.auth.auth_repositories import UserRepository


class UsernameAlreadyExistsError(Exception):
    pass


class AuthService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    async def create_user(
        self,
        username: str,
        password: str,
        session: AsyncSession
    ) -> User:
        username = username.strip().lower()
        try:
            if await self.repo.get_by_username(session, username) is not None:
                raise UsernameAlreadyExistsError

            user = User(
                username=username,
                role=UserRole.USER,
                hashed_password=hash_password(password),
            )
            db_user = await self.repo.create_user(session, map_to_model(user))
            result = map_to_domain(db_user)
            await session.commit()
            return result
        except IntegrityError as exc:
            await session.rollback()
            if await self.repo.get_by_username(session, username) is not None:
                raise UsernameAlreadyExistsError from exc
            raise
        except Exception:
            await session.rollback()
            raise

    # async def get_by_username(
    #     self,
    #     username: str,
    #     session: AsyncSession,
    # ) -> User | None:
    #     username=username.strip().lower()
    #     try:
    #         result = await self.repo.get_by_username(session, username)
    #         if result is None:
    #             return None

    #         return result


auth_service = AuthService(SQLAlchemyUserRepository())
