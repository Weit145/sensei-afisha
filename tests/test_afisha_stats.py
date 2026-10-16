import asyncio
import os
import unittest
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import delete, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from src.core.config import settings
from src.domain.err import NotFoundError
from src.repositories.storage.models import AfishaModel, AfishaStatsModel, UserModel
from src.repositories.storage.models.user import user_afisha_follows
from src.usecase.afisha.afisha_stats_service import afisha_stats_service


@unittest.skipUnless(
    os.getenv("RUN_AUTH_DB_TESTS") == "1",
    "Set RUN_AUTH_DB_TESTS=1 for PostgreSQL tests",
)
class AfishaStatsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        url = make_url(settings.database_url)
        self.name = "codex_stats_test_" + uuid4().hex
        self.admin = create_async_engine(url, isolation_level="AUTOCOMMIT")
        self.addAsyncCleanup(self.admin.dispose)
        async with self.admin.connect() as connection:
            await connection.execute(text(f'CREATE DATABASE "{self.name}"'))
        self.addAsyncCleanup(self.drop_database)
        self.engine = create_async_engine(url.set(database=self.name))
        self.addAsyncCleanup(self.engine.dispose)
        self.factory = async_sessionmaker(self.engine, expire_on_commit=False)
        await self.migrate("20261016_01")
        self.users = [uuid4() for _ in range(6)]
        self.afishas = [uuid4(), uuid4()]
        async with self.engine.begin() as connection:
            await connection.execute(
                insert(UserModel),
                [
                    {"id": user_id, "username": f"user_{index}", "role": "user"}
                    for index, user_id in enumerate(self.users)
                ],
            )
            await connection.execute(
                insert(AfishaModel),
                [self.afisha_values(afisha_id) for afisha_id in self.afishas],
            )
            await connection.execute(
                insert(user_afisha_follows).values(
                    user_id=self.users[0], afisha_id=self.afishas[0]
                )
            )
        await self.migrate("head")

    async def drop_database(self):
        async with self.admin.connect() as connection:
            await connection.execute(text(f'DROP DATABASE "{self.name}" WITH (FORCE)'))

    async def migrate(self, revision, *, downgrade=False):
        config = Config("alembic.ini")
        async with self.engine.begin() as connection:

            def run(sync_connection):
                config.attributes["connection"] = sync_connection
                (command.downgrade if downgrade else command.upgrade)(config, revision)

            await connection.run_sync(run)

    def afisha_values(self, afisha_id):
        return {
            "id": afisha_id,
            "title": "Test afisha",
            "starts_at": datetime.now(UTC),
            "ends_at": datetime.now(UTC) + timedelta(hours=1),
        }

    async def count(self, afisha_id):
        async with self.engine.connect() as connection:
            return await connection.scalar(
                select(AfishaStatsModel.followers_count).where(
                    AfishaStatsModel.afisha_id == afisha_id
                )
            )

    async def follow(self, user_id, afisha_id):
        async with self.engine.begin() as connection:
            await connection.execute(
                insert(user_afisha_follows)
                .values(user_id=user_id, afisha_id=afisha_id)
                .on_conflict_do_nothing()
            )

    async def unfollow(self, user_id, afisha_id):
        async with self.engine.begin() as connection:
            await connection.execute(
                delete(user_afisha_follows).where(
                    user_afisha_follows.c.user_id == user_id,
                    user_afisha_follows.c.afisha_id == afisha_id,
                )
            )

    async def test_service_reads_stats_and_reports_missing_afisha(self):
        async with self.factory() as session:
            for afisha_id, expected in zip(self.afishas, (1, 0), strict=True):
                result = await afisha_stats_service.get_stats_by_afisha_id(
                    afisha_id=afisha_id, session=session
                )
                self.assertEqual(result.afisha_id, afisha_id)
                self.assertEqual(result.followers_count, expected)
            with self.assertRaises(NotFoundError):
                await afisha_stats_service.get_stats_by_afisha_id(
                    afisha_id=uuid4(), session=session
                )

    async def test_backfill_new_afisha_and_orm_relationship(self):
        self.assertEqual(await self.count(self.afishas[0]), 1)
        self.assertEqual(await self.count(self.afishas[1]), 0)
        self.assertEqual(
            set(AfishaStatsModel.__table__.columns.keys()),
            {"afisha_id", "followers_count"},
        )
        async with self.factory() as session:
            afisha = await session.scalar(
                select(AfishaModel)
                .where(AfishaModel.id == self.afishas[0])
                .options(selectinload(AfishaModel.stats))
            )
            self.assertEqual(afisha.stats.followers_count, 1)
        new_id = uuid4()
        async with self.engine.begin() as connection:
            await connection.execute(
                insert(AfishaModel).values(**self.afisha_values(new_id))
            )
        self.assertEqual(await self.count(new_id), 0)

    async def test_duplicates_unfollow_and_rollback(self):
        afisha_id = self.afishas[0]
        await self.follow(self.users[0], afisha_id)
        self.assertEqual(await self.count(afisha_id), 1)
        await self.follow(self.users[1], afisha_id)
        self.assertEqual(await self.count(afisha_id), 2)
        async with self.engine.connect() as connection:
            await connection.execute(
                insert(user_afisha_follows).values(
                    user_id=self.users[2], afisha_id=afisha_id
                )
            )
            self.assertEqual(
                await connection.scalar(
                    select(AfishaStatsModel.followers_count).where(
                        AfishaStatsModel.afisha_id == afisha_id
                    )
                ),
                3,
            )
            await connection.rollback()
        self.assertEqual(await self.count(afisha_id), 2)
        await self.unfollow(self.users[1], afisha_id)
        await self.unfollow(self.users[1], afisha_id)
        self.assertEqual(await self.count(afisha_id), 1)
        await self.unfollow(self.users[0], afisha_id)
        self.assertEqual(await self.count(afisha_id), 0)

    async def test_user_and_afisha_cascade_deletes(self):
        await self.follow(self.users[0], self.afishas[1])
        await self.follow(self.users[1], self.afishas[0])
        async with self.engine.begin() as connection:
            await connection.execute(
                delete(UserModel).where(UserModel.id == self.users[0])
            )
        self.assertEqual(await self.count(self.afishas[0]), 1)
        self.assertEqual(await self.count(self.afishas[1]), 0)
        async with self.engine.begin() as connection:
            await connection.execute(
                delete(AfishaModel).where(AfishaModel.id == self.afishas[0])
            )
        self.assertIsNone(await self.count(self.afishas[0]))
        self.assertEqual(await self.count(self.afishas[1]), 0)

    async def test_parallel_follows_and_unfollows(self):
        afisha_id = self.afishas[0]
        await asyncio.wait_for(
            asyncio.gather(
                *(self.follow(user_id, afisha_id) for user_id in self.users[1:])
            ),
            timeout=20,
        )
        self.assertEqual(await self.count(afisha_id), 6)
        await asyncio.wait_for(
            asyncio.gather(*(self.follow(self.users[0], afisha_id) for _ in range(4))),
            timeout=20,
        )
        self.assertEqual(await self.count(afisha_id), 6)
        await asyncio.wait_for(
            asyncio.gather(
                *(self.unfollow(user_id, afisha_id) for user_id in self.users[1:])
            ),
            timeout=20,
        )
        self.assertEqual(await self.count(afisha_id), 1)

    async def test_update_and_truncate(self):
        async with self.engine.begin() as connection:
            await connection.execute(
                update(user_afisha_follows)
                .values(afisha_id=self.afishas[1])
                .where(user_afisha_follows.c.user_id == self.users[0])
            )
        self.assertEqual(await self.count(self.afishas[0]), 0)
        self.assertEqual(await self.count(self.afishas[1]), 1)
        async with self.engine.begin() as connection:
            await connection.execute(
                update(user_afisha_follows)
                .values(user_id=self.users[1])
                .where(user_afisha_follows.c.user_id == self.users[0])
            )
        self.assertEqual(await self.count(self.afishas[1]), 1)
        async with self.engine.begin() as connection:
            await connection.execute(text("TRUNCATE user_afisha_follows"))
        self.assertEqual(await self.count(self.afishas[0]), 0)
        self.assertEqual(await self.count(self.afishas[1]), 0)

    async def test_downgrade_and_rebuild_preserve_follows(self):
        await self.follow(self.users[1], self.afishas[0])
        await self.migrate("20261016_01", downgrade=True)
        await self.migrate("head")
        self.assertEqual(await self.count(self.afishas[0]), 2)
        await self.follow(self.users[2], self.afishas[0])
        self.assertEqual(await self.count(self.afishas[0]), 3)


if __name__ == "__main__":
    unittest.main()
