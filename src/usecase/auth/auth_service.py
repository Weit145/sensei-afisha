from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from hmac import compare_digest
from typing import Any, Literal
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.domain.err import NotFoundError
from src.domain.user import User, UserRole
from src.infrastructure.jwt import (
    create_refresh_token,
    create_token,
    decode_token,
    hash_refresh_token,
)
from src.infrastructure.password import hash_password, verify_password
from src.repositories.storage.map.user import map_to_domain, map_to_model
from src.repositories.storage.models.user import UserSessionModel
from src.repositories.storage.postgres.user.user_repository import (
    SQLAlchemyUserRepository,
)
from src.repositories.storage.postgres.user.user_session_repository import (
    SQLAlchemyUserSessionRepository,
)
from src.usecase.auth.dto.auth import AuthResult
from src.usecase.port.auth.auth_repositories import UserRepository
from src.usecase.port.auth.session_repositories import UserSessionRepository


class UsernameAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


class AuthService:
    def __init__(self, repo: UserRepository, sessions: UserSessionRepository) -> None:
        self.repo = repo
        self.sessions = sessions

    async def create_user(
        self, username: str, password: str, session: AsyncSession
    ) -> AuthResult:
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
            result = await self._create_session(map_to_domain(db_user), session)
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

    async def login(
        self, username: str, password: str, session: AsyncSession
    ) -> AuthResult:
        try:
            db_user = await self.repo.get_by_username(session, username.strip().lower())
            valid_password = verify_password(
                password, db_user.hashed_password if db_user is not None else None
            )
            if db_user is None or not valid_password:
                raise InvalidCredentialsError
            result = await self._create_session(map_to_domain(db_user), session)
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            raise

    async def refresh(self, token: str, session: AsyncSession) -> AuthResult:
        payload = self._decode(token, "refresh")
        try:
            user_session = await self.sessions.get_by_id(
                session, UUID(payload["sid"]), for_update=True
            )
            user_session = self._require_active_session(
                user_session, UUID(payload["sub"])
            )
            if not compare_digest(
                user_session.refresh_token_hash, hash_refresh_token(token)
            ):
                user_session.revoked_at = datetime.now(UTC)
                await session.commit()
                raise InvalidTokenError
            db_user = await self.repo.get_by_user_id(session, user_session.user_id)
            if db_user is None:
                raise InvalidTokenError
            result = self._issue_tokens(map_to_domain(db_user), user_session)
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            raise

    async def logout(self, token: str | None, session: AsyncSession) -> None:
        if token is None:
            return
        try:
            payload = self._decode(token, "refresh")
        except InvalidTokenError:
            return
        try:
            user_session = await self.sessions.get_by_id(
                session, UUID(payload["sid"]), for_update=True
            )
            if user_session is not None and user_session.user_id == UUID(
                payload["sub"]
            ):
                user_session.revoked_at = datetime.now(UTC)
                await session.commit()
        except Exception:
            await session.rollback()
            raise

    async def get_current_user(self, token: str, session: AsyncSession) -> User:
        payload = self._decode(token, "access")
        user_session = await self.sessions.get_by_id(session, UUID(payload["sid"]))
        user_session = self._require_active_session(user_session, UUID(payload["sub"]))
        db_user = await self.repo.get_by_user_id(session, user_session.user_id)
        if db_user is None:
            raise InvalidTokenError
        return map_to_domain(db_user)

    async def get_followed_afisha_ids(
        self, user_id: UUID, session: AsyncSession
    ) -> list[UUID]:
        return await self.repo.get_followed_afisha_ids(session, user_id)

    async def get_user_contacts(self, user_id: UUID, session: AsyncSession) -> User:
        db_user = await self.repo.get_by_user_id(session, user_id)
        if db_user is None:
            raise NotFoundError("Пользователь не найден")
        return map_to_domain(db_user)

    async def update_contacts(
        self,
        user_id: UUID,
        contacts: Mapping[str, str | None],
        session: AsyncSession,
    ) -> User:
        try:
            db_user = await self.repo.get_by_user_id(session, user_id)
            if db_user is None:
                raise InvalidTokenError
            if "tg_url" in contacts:
                db_user.tg_url = contacts["tg_url"]
            if "vk_url" in contacts:
                db_user.vk_url = contacts["vk_url"]
            await session.commit()
            return map_to_domain(db_user)
        except Exception:
            await session.rollback()
            raise

    async def _create_session(self, user: User, session: AsyncSession) -> AuthResult:
        user_session = UserSessionModel(
            id=uuid4(),
            user_id=user.id,
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.refresh_token_expire_days),
        )
        result = self._issue_tokens(user, user_session)
        await self.sessions.create_session(session, user_session)
        return result

    @staticmethod
    def _issue_tokens(user: User, user_session: UserSessionModel) -> AuthResult:
        refresh_token = create_refresh_token(
            user.id, user_session.id, user_session.expires_at
        )
        user_session.refresh_token_hash = hash_refresh_token(refresh_token)
        return AuthResult(
            user=user,
            access_token=create_token(user.id, user.role, user_session.id),
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
            refresh_expires_at=user_session.expires_at,
        )

    @staticmethod
    def _decode(token: str, token_type: Literal["access", "refresh"]) -> dict[str, Any]:
        try:
            return decode_token(token, token_type)
        except ValueError as exc:
            raise InvalidTokenError from exc

    @staticmethod
    def _require_active_session(
        user_session: UserSessionModel | None, user_id: UUID
    ) -> UserSessionModel:
        if (
            user_session is None
            or user_session.user_id != user_id
            or user_session.revoked_at is not None
            or user_session.expires_at <= datetime.now(UTC)
        ):
            raise InvalidTokenError
        return user_session


auth_service = AuthService(
    SQLAlchemyUserRepository(), SQLAlchemyUserSessionRepository()
)
