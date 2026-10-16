import asyncio
import os
import unittest
from unittest.mock import patch
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.core.config import Settings, settings
from src.infrastructure.password import hash_password, verify_password
from src.repositories.storage.models import UserModel
from src.scripts.create_admin import create_admin
from src.usecase.auth.auth_service import auth_service


class AdminConfigTests(unittest.TestCase):
    def test_password_from_environment_is_masked(self):
        password = "test-admin-environment-password"
        with patch.dict(os.environ, {"ADMIN_PASSWORD": password}):
            config = Settings(_env_file=None, JWT_SECRET_KEY="x" * 32)
        self.assertEqual(config.admin_password.get_secret_value(), password)
        self.assertNotIn(password, repr(config))
        self.assertNotIn(password, config.model_dump_json())


@unittest.skipUnless(
    os.getenv("RUN_AUTH_DB_TESTS") == "1",
    "Set RUN_AUTH_DB_TESTS=1 for PostgreSQL tests",
)
class CreateAdminTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        url = make_url(settings.database_url)
        self.name = "codex_admin_test_" + uuid4().hex
        self.admin = create_async_engine(url, isolation_level="AUTOCOMMIT")
        self.addAsyncCleanup(self.admin.dispose)
        async with self.admin.connect() as connection:
            await connection.execute(text(f'CREATE DATABASE "{self.name}"'))
        self.addAsyncCleanup(self.drop_database)
        self.engine = create_async_engine(url.set(database=self.name))
        self.addAsyncCleanup(self.engine.dispose)
        self.factory = async_sessionmaker(self.engine, expire_on_commit=False)
        config = Config("alembic.ini")
        async with self.engine.begin() as connection:

            def migrate(sync_connection):
                config.attributes["connection"] = sync_connection
                command.upgrade(config, "head")

            await connection.run_sync(migrate)

    async def drop_database(self):
        async with self.admin.connect() as connection:
            await connection.execute(text(f'DROP DATABASE "{self.name}" WITH (FORCE)'))

    async def seed(self, password="test-admin-password"):
        async with self.factory() as session:
            return await create_admin(session, password)

    async def test_creation_login_and_repeated_run(self):
        self.assertTrue(await self.seed())
        async with self.factory() as session:
            result = await auth_service.login("admin", "test-admin-password", session)
            self.assertEqual(result.user.role, "admin")
            original_id = result.user.id
            original_hash = result.user.hashed_password
        self.assertFalse(await self.seed("different-password"))
        self.assertFalse(await self.seed(None))
        async with self.factory() as session:
            self.assertEqual(
                await session.scalar(select(func.count()).select_from(UserModel)), 1
            )
            user = await session.scalar(select(UserModel))
            self.assertEqual(user.id, original_id)
            self.assertEqual(user.hashed_password, original_hash)
            self.assertTrue(
                verify_password("test-admin-password", user.hashed_password)
            )
            self.assertFalse(
                verify_password("different-password", user.hashed_password)
            )
            self.assertEqual(
                (await auth_service.get_current_user(result.access_token, session)).id,
                original_id,
            )

    async def test_concurrent_runs_create_one_account(self):
        results = await asyncio.wait_for(
            asyncio.gather(*(self.seed() for _ in range(5))), timeout=30
        )
        self.assertEqual(results.count(True), 1)
        self.assertEqual(results.count(False), 4)
        async with self.factory() as session:
            self.assertEqual(
                await session.scalar(select(func.count()).select_from(UserModel)), 1
            )

    async def test_missing_or_invalid_password_does_not_create_account(self):
        for password in (None, "", "short", " " * 10, "a" * 129):
            with (
                self.subTest(
                    password_length=None if password is None else len(password)
                ),
                self.assertRaisesRegex(ValueError, "ADMIN_PASSWORD"),
            ):
                await self.seed(password)
        async with self.factory() as session:
            self.assertEqual(
                await session.scalar(select(func.count()).select_from(UserModel)), 0
            )

    async def test_existing_regular_user_is_not_promoted(self):
        original_hash = hash_password("regular-user-password")
        async with self.factory.begin() as session:
            session.add(
                UserModel(username="admin", role="user", hashed_password=original_hash)
            )
        with self.assertRaisesRegex(ValueError, "non-admin"):
            await self.seed()
        async with self.factory() as session:
            user = await session.scalar(select(UserModel))
            self.assertEqual(user.role, "user")
            self.assertEqual(user.hashed_password, original_hash)


if __name__ == "__main__":
    unittest.main()
