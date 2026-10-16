"""Pagination checks; PostgreSQL tests require DISCUSSION_TEST_DATABASE_URL."""

# Settings are loaded when importing the discussion router.
import base64
import json
import os
import unittest
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

os.environ.setdefault("JWT_SECRET_KEY", "discussion-pagination-tests-only-secret")

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.domain.user import UserRole
from src.infrastructure.jwt import create_token
from src.repositories.storage.models import (
    AfishaModel,
    MessageModel,
    UserModel,
    UserSessionModel,
)
from src.repositories.storage.postgres.db_helper import db_helper
from src.transport.api.v1.handler.discussion.message import router
from src.transport.api.v1.map.discussion.message import decode_cursor, encode_cursor
from src.usecase.discussion.dto.message import MessageCursor

TEST_DATABASE_URL = os.environ.get("DISCUSSION_TEST_DATABASE_URL")
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CursorTests(unittest.TestCase):
    def test_round_trip_preserves_timestamp_and_ids(self):
        cursor = MessageCursor(
            afisha_id=uuid.uuid4(),
            created_at=datetime(2026, 10, 16, 12, 30, 45, 123456, tzinfo=UTC),
            id=uuid.uuid4(),
        )
        self.assertEqual(decode_cursor(encode_cursor(cursor), cursor.afisha_id), cursor)

    def test_rejects_other_concert(self):
        cursor = MessageCursor(
            afisha_id=uuid.uuid4(), created_at=datetime.now(UTC), id=uuid.uuid4()
        )
        with self.assertRaises(ValueError):
            decode_cursor(encode_cursor(cursor), uuid.uuid4())

    def test_rejects_invalid_payloads(self):
        afisha_id = uuid.uuid4()
        invalid_json = [
            {},
            [],
            {
                "afisha_id": str(afisha_id),
                "id": str(uuid.uuid4()),
                "created_at": "2026-10-16T12:00:00",
            },
            {
                "afisha_id": str(afisha_id),
                "id": "not-a-uuid",
                "created_at": "2026-10-16T12:00:00Z",
            },
        ]
        values = ["!invalid!", "not-base64", "", "юникод"] + [
            base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
            for payload in invalid_json
        ]
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                decode_cursor(value, afisha_id)


@unittest.skipUnless(
    TEST_DATABASE_URL, "Set DISCUSSION_TEST_DATABASE_URL for PostgreSQL tests"
)
class PaginationPostgresTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.schema = "discussion_pagination_test_" + uuid.uuid4().hex
        self.admin_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
        async with self.admin_engine.begin() as connection:
            await connection.exec_driver_sql(f'CREATE SCHEMA "{self.schema}"')
        self.engine = create_async_engine(
            TEST_DATABASE_URL,
            poolclass=NullPool,
            connect_args={"server_settings": {"search_path": self.schema}},
        )
        self.addAsyncCleanup(self.cleanup)
        async with self.engine.begin() as connection:
            await connection.run_sync(self.upgrade)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        self.app = FastAPI()
        self.app.include_router(router, prefix="/api")

        async def get_session():
            async with self.sessions() as session:
                try:
                    yield session
                except Exception:
                    await session.rollback()
                    raise

        self.app.dependency_overrides[db_helper.get_session] = get_session
        self.author_id = uuid.uuid4()
        self.session_id = uuid.uuid4()
        self.afisha_id = uuid.uuid4()
        self.other_afisha_id = uuid.uuid4()
        self.timestamp = datetime.now(UTC) - timedelta(days=1)
        async with self.sessions() as session:
            session.add(
                UserModel(id=self.author_id, username="pagination-test", role="user")
            )
            session.add_all(
                [
                    AfishaModel(
                        id=concert_id,
                        title="Pagination concert",
                        description="Test",
                        starts_at=self.timestamp,
                        ends_at=self.timestamp + timedelta(hours=1),
                    )
                    for concert_id in (self.afisha_id, self.other_afisha_id)
                ]
            )
            await session.flush()
            session.add(
                UserSessionModel(
                    id=self.session_id,
                    user_id=self.author_id,
                    refresh_token_hash="0" * 64,
                    expires_at=datetime.now(UTC) + timedelta(days=1),
                )
            )
            await session.commit()

    @staticmethod
    def upgrade(connection):
        config = Config(str(PROJECT_ROOT / "alembic.ini"))
        config.set_main_option("path_separator", "os")
        config.attributes["connection"] = connection
        command.upgrade(config, "head")

    async def cleanup(self):
        await self.engine.dispose()
        async with self.admin_engine.begin() as connection:
            await connection.exec_driver_sql(f'DROP SCHEMA "{self.schema}" CASCADE')
        await self.admin_engine.dispose()

    async def seed(self, count, *, afisha_id=None, same_time=False):
        async with self.sessions() as session:
            session.add_all(
                [
                    MessageModel(
                        id=uuid.UUID(int=index + 1),
                        afisha_id=afisha_id or self.afisha_id,
                        author_id=self.author_id,
                        text=f"Message {index + 1}",
                        created_at=self.timestamp
                        if same_time
                        else self.timestamp + timedelta(seconds=index),
                    )
                    for index in reversed(range(count))
                ]
            )
            await session.commit()

    async def request(
        self, *, afisha_id=None, params=None, method="GET", body=None, token=None
    ):
        path = f"/api/afisha/{afisha_id or self.afisha_id}/messages"
        payload = json.dumps(body).encode() if body is not None else b""
        headers = [(b"content-type", b"application/json")]
        if token is not None:
            headers.append((b"authorization", f"Bearer {token}".encode()))
        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.4"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": urlencode(params or {}).encode(),
            "root_path": "",
            "headers": headers,
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
        }
        responses = []

        async def receive():
            return {"type": "http.request", "body": payload, "more_body": False}

        async def send(message):
            responses.append(message)

        await self.app(scope, receive, send)
        status = next(
            item["status"]
            for item in responses
            if item["type"] == "http.response.start"
        )
        content = b"".join(
            item.get("body", b"")
            for item in responses
            if item["type"] == "http.response.body"
        )
        return status, json.loads(content)

    async def test_default_returns_only_latest_50_in_chronological_order(self):
        await self.seed(105)
        status, page = await self.request()
        self.assertEqual(status, 200)
        self.assertEqual(
            [item["text"] for item in page["items"]],
            [f"Message {index}" for index in range(56, 106)],
        )
        self.assertTrue(page["has_more"])
        self.assertIsNotNone(page["next_cursor"])

    async def test_all_pages_with_equal_timestamps_have_no_gaps_or_duplicates(self):
        await self.seed(7, same_time=True)
        params = {"limit": 3}
        pages = []
        while True:
            status, page = await self.request(params=params)
            self.assertEqual(status, 200)
            pages.append([item["text"] for item in page["items"]])
            if not page["has_more"]:
                self.assertIsNone(page["next_cursor"])
                break
            self.assertIsNotNone(page["next_cursor"])
            params["before"] = page["next_cursor"]
            self.assertLess(len(pages), 4)
        self.assertEqual(
            pages,
            [
                ["Message 5", "Message 6", "Message 7"],
                ["Message 2", "Message 3", "Message 4"],
                ["Message 1"],
            ],
        )

    async def test_empty_history_and_exact_page_boundary(self):
        status, page = await self.request()
        self.assertEqual(status, 200)
        self.assertEqual(page, {"items": [], "next_cursor": None, "has_more": False})
        await self.seed(2)
        _, page = await self.request(params={"limit": 2})
        self.assertEqual(len(page["items"]), 2)
        self.assertFalse(page["has_more"])
        self.assertIsNone(page["next_cursor"])

    async def test_new_message_does_not_shift_older_page(self):
        await self.seed(5)
        _, page = await self.request(params={"limit": 2})
        for role in ("user", "admin"):
            async with self.sessions() as session:
                await session.execute(
                    update(UserModel)
                    .where(UserModel.id == self.author_id)
                    .values(role=role)
                )
                await session.commit()
            status, sent = await self.request(
                method="POST",
                body={"text": f"New {role}"},
                token=create_token(self.author_id, UserRole(role), self.session_id),
            )
            self.assertEqual(status, 201)
            self.assertEqual(sent["author_id"], str(self.author_id))
        _, older = await self.request(
            params={"limit": 2, "before": page["next_cursor"]}
        )
        self.assertEqual(
            [item["text"] for item in older["items"]], ["Message 2", "Message 3"]
        )
        status, _ = await self.request(method="POST", body={"text": "Guest"})
        self.assertEqual(status, 401)

    async def test_cursor_still_works_when_boundary_message_is_removed(self):
        await self.seed(5)
        _, page = await self.request(params={"limit": 2})
        async with self.sessions() as session:
            await session.execute(
                delete(MessageModel).where(MessageModel.id == uuid.UUID(int=4))
            )
            await session.commit()
        _, older = await self.request(
            params={"limit": 2, "before": page["next_cursor"]}
        )
        self.assertEqual(
            [item["text"] for item in older["items"]], ["Message 2", "Message 3"]
        )

    async def test_history_and_cursor_are_scoped_to_concert(self):
        await self.seed(3)
        _, page = await self.request(params={"limit": 2})
        status, other_page = await self.request(afisha_id=self.other_afisha_id)
        self.assertEqual(status, 200)
        self.assertEqual(other_page["items"], [])
        status, _ = await self.request(
            afisha_id=self.other_afisha_id, params={"before": page["next_cursor"]}
        )
        self.assertEqual(status, 422)

    async def test_limit_bounds_and_invalid_cursors(self):
        await self.seed(105)
        for limit in (0, -1, 101, "invalid"):
            with self.subTest(limit=limit):
                status, _ = await self.request(params={"limit": limit})
                self.assertEqual(status, 422)
        for before in ("", "!invalid!", "x" * 513):
            with self.subTest(before=before[:10]):
                status, _ = await self.request(params={"before": before})
                self.assertEqual(status, 422)
        _, page = await self.request(params={"limit": 100})
        self.assertEqual(len(page["items"]), 100)
        self.assertTrue(page["has_more"])
        _, page = await self.request(params={"limit": 1})
        self.assertEqual([item["text"] for item in page["items"]], ["Message 105"])

    async def test_cursor_before_all_messages_and_missing_concert(self):
        await self.seed(2)
        before = encode_cursor(
            MessageCursor(
                afisha_id=self.afisha_id,
                created_at=self.timestamp - timedelta(seconds=1),
                id=uuid.uuid4(),
            )
        )
        _, page = await self.request(params={"before": before})
        self.assertEqual(page, {"items": [], "next_cursor": None, "has_more": False})
        status, _ = await self.request(afisha_id=uuid.uuid4())
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
