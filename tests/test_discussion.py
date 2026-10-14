"""Run with unittest; PostgreSQL checks require DISCUSSION_TEST_DATABASE_URL."""

# The test secret must be set before importing application settings.

import json
import os
import unittest
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

os.environ.setdefault("JWT_SECRET_KEY", "discussion-tests-only-secret")

from alembic import command
from alembic.config import Config
from jose import jwt
from pydantic import ValidationError
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.config import settings
from src.domain.discussion.message import Message
from src.domain.err import InvalidDataError
from src.infrastructure.jwt import create_token
from src.main import app
from src.repositories.storage.models import AfishaModel, MessageModel
from src.repositories.storage.postgres.db_helper import db_helper
from src.transport.api.v1.schemas.discussion.message import CreateMessage

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_DATABASE_URL = os.environ.get("DISCUSSION_TEST_DATABASE_URL")


class MessageValidationTests(unittest.TestCase):
    def test_whitespace_and_length(self):
        for value in ("", " \n\t ", "x" * 2001):
            with self.subTest(value=value[:20]):
                with self.assertRaises(ValidationError):
                    CreateMessage(text=value)
                with self.assertRaises(InvalidDataError):
                    Message(afisha_id=uuid.uuid4(), author_id=uuid.uuid4(), text=value)
        self.assertEqual(CreateMessage(text="  Привет\n ").text, "Привет")
        self.assertEqual(CreateMessage(text="x" * 2000).text, "x" * 2000)

    def test_author_cannot_be_supplied_in_body(self):
        with self.assertRaises(ValidationError):
            CreateMessage.model_validate(
                {"text": "Hello", "author_id": str(uuid.uuid4())}
            )


@unittest.skipUnless(
    TEST_DATABASE_URL, "Set DISCUSSION_TEST_DATABASE_URL for PostgreSQL tests"
)
class DiscussionPostgresTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # All data and Alembic state live in a unique schema, never in public.
        self.schema = "discussion_test_" + uuid.uuid4().hex
        self.admin_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
        async with self.admin_engine.begin() as connection:
            await connection.exec_driver_sql(f'CREATE SCHEMA "{self.schema}"')
        self.engine = create_async_engine(
            TEST_DATABASE_URL,
            poolclass=NullPool,
            connect_args={"server_settings": {"search_path": self.schema}},
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        self.previous_overrides = dict(app.dependency_overrides)
        self.addAsyncCleanup(self.cleanup)
        await self.migrate("upgrade", "head")

        async def get_session():
            async with self.sessions() as session:
                try:
                    yield session
                except Exception:
                    await session.rollback()
                    raise

        app.dependency_overrides[db_helper.get_session] = get_session
        self.author_id = uuid.uuid4()
        self.afisha_id = uuid.uuid4()
        self.other_afisha_id = uuid.uuid4()
        now = datetime.now(UTC)
        async with self.sessions() as session:
            # Seed the actual migrated users schema, which predates the auth model.
            await session.execute(
                text(
                    "INSERT INTO users (id, name, ip, created_at) VALUES (:id, :name, :ip, :now)"
                ),
                {
                    "id": self.author_id,
                    "name": "Test user",
                    "ip": "127.0.0.1",
                    "now": now,
                },
            )
            session.add_all(
                [
                    AfishaModel(
                        id=concert_id,
                        title="Test concert",
                        description="Concert",
                        starts_at=now,
                        ends_at=now + timedelta(hours=1),
                    )
                    for concert_id in (self.afisha_id, self.other_afisha_id)
                ]
            )
            await session.commit()

    async def cleanup(self):
        app.dependency_overrides.clear()
        app.dependency_overrides.update(self.previous_overrides)
        await self.engine.dispose()
        async with self.admin_engine.begin() as connection:
            await connection.exec_driver_sql(f'DROP SCHEMA "{self.schema}" CASCADE')
        await self.admin_engine.dispose()

    async def migrate(self, operation, revision):
        def run(connection):
            config = Config(str(PROJECT_ROOT / "alembic.ini"))
            config.set_main_option("path_separator", "os")
            config.attributes["connection"] = connection
            getattr(command, operation)(config, revision)

        async with self.engine.begin() as connection:
            await connection.run_sync(run)

    async def request(self, method, afisha_id=None, body=None, token=None):
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
            "query_string": b"",
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

        await app(scope, receive, send)
        response = next(
            item for item in responses if item["type"] == "http.response.start"
        )
        content = b"".join(
            item.get("body", b"")
            for item in responses
            if item["type"] == "http.response.body"
        )
        return response["status"], json.loads(content)

    def token(self, role="user", author_id=None):
        return create_token(str(author_id or self.author_id), role)

    async def test_public_empty_history(self):
        status, body = await self.request("GET")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"items": []})

    async def test_guest_and_invalid_tokens_cannot_send(self):
        expired = jwt.encode(
            {"user_id": str(self.author_id), "role": "user", "exp": 1},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        missing_claims = jwt.encode(
            {"exp": datetime.now(UTC) + timedelta(minutes=5)},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        for token in (None, "not-a-token", expired, missing_claims):
            with self.subTest(token=token is not None):
                status, _ = await self.request(
                    "POST", body={"text": "Hello"}, token=token
                )
                self.assertEqual(status, 401)
        _, history = await self.request("GET")
        self.assertEqual(history["items"], [])

    async def test_user_and_admin_send_and_messages_survive_new_connections(self):
        for role in ("user", "admin"):
            status, body = await self.request(
                "POST", body={"text": f"  Привет от {role}  "}, token=self.token(role)
            )
            self.assertEqual(status, 201)
            self.assertEqual(body["author_id"], str(self.author_id))
            self.assertEqual(body["afisha_id"], str(self.afisha_id))
            self.assertEqual(body["text"], f"Привет от {role}")
            self.assertIsNotNone(uuid.UUID(body["id"]))
            self.assertIsNotNone(datetime.fromisoformat(body["created_at"]).tzinfo)
        # Dispose all connections; the next request must read committed rows from PostgreSQL.
        await self.engine.dispose()
        status, history = await self.request("GET")
        self.assertEqual(status, 200)
        self.assertEqual(
            [item["text"] for item in history["items"]],
            ["Привет от user", "Привет от admin"],
        )

    async def test_concert_isolation(self):
        await self.request("POST", body={"text": "First concert"}, token=self.token())
        await self.request(
            "POST",
            afisha_id=self.other_afisha_id,
            body={"text": "Second concert"},
            token=self.token(),
        )
        for concert_id, expected in (
            (self.afisha_id, "First concert"),
            (self.other_afisha_id, "Second concert"),
        ):
            _, history = await self.request("GET", afisha_id=concert_id)
            self.assertEqual([item["text"] for item in history["items"]], [expected])

    async def test_missing_concert_and_missing_author(self):
        missing_id = uuid.uuid4()
        for method in ("GET", "POST"):
            status, _ = await self.request(
                method, afisha_id=missing_id, body={"text": "Hello"}, token=self.token()
            )
            self.assertEqual(status, 404)
        status, _ = await self.request(
            "POST", body={"text": "Hello"}, token=self.token(author_id=missing_id)
        )
        self.assertEqual(status, 401)

    async def test_invalid_body_and_uuid(self):
        for body in (
            {},
            {"text": " \t\n "},
            {"text": "x" * 2001},
            {"text": "Hello", "author_id": str(uuid.uuid4())},
            {"text": 123},
        ):
            with self.subTest(body=str(body)[:40]):
                status, _ = await self.request("POST", body=body, token=self.token())
                self.assertEqual(status, 422)
        status, _ = await self.request("GET", afisha_id="not-a-uuid")
        self.assertEqual(status, 422)

    async def test_history_ties_are_sorted_by_id(self):
        timestamp = datetime.now(UTC)
        ids = [uuid.UUID(int=3), uuid.UUID(int=1), uuid.UUID(int=2)]
        async with self.sessions() as session:
            session.add_all(
                [
                    MessageModel(
                        id=message_id,
                        afisha_id=self.afisha_id,
                        author_id=self.author_id,
                        text="Same time",
                        created_at=timestamp,
                    )
                    for message_id in ids
                ]
            )
            await session.commit()
        _, history = await self.request("GET")
        self.assertEqual(
            [item["id"] for item in history["items"]],
            [str(message_id) for message_id in sorted(ids)],
        )

    async def test_foreign_keys_text_constraints_and_restrict_deletion(self):
        for changes in (
            {"afisha_id": uuid.uuid4()},
            {"author_id": uuid.uuid4()},
            {"text": "   "},
            {"text": "\t\n\r"},
            {"text": "x" * 2001},
        ):
            fields = {
                "id": uuid.uuid4(),
                "afisha_id": self.afisha_id,
                "author_id": self.author_id,
                "text": "Hello",
            }
            fields.update(changes)
            async with self.sessions() as session:
                session.add(MessageModel(**fields))
                with self.assertRaises(IntegrityError):
                    await session.commit()
        await self.request("POST", body={"text": "Keep history"}, token=self.token())
        for table, row_id in (("afisha", self.afisha_id), ("users", self.author_id)):
            async with self.sessions() as session:
                with self.assertRaises(IntegrityError):
                    await session.execute(
                        text(f"DELETE FROM {table} WHERE id = :id"), {"id": row_id}
                    )
                    await session.commit()

    async def test_failed_commit_does_not_leave_a_message(self):
        from unittest.mock import AsyncMock, patch

        from src.transport.api.v1.handler.discussion.message import message_service

        with (
            patch.object(
                message_service.repo, "commit", new=AsyncMock(side_effect=RuntimeError)
            ),
            self.assertRaises(RuntimeError),
        ):
            await self.request(
                "POST", body={"text": "Not committed"}, token=self.token()
            )
        async with self.sessions() as session:
            self.assertEqual(list(await session.scalars(select(MessageModel))), [])

    async def test_migration_round_trip(self):
        await self.migrate("downgrade", "20261014_02")
        async with self.engine.connect() as connection:
            tables = await connection.run_sync(
                lambda conn: inspect(conn).get_table_names()
            )
            self.assertNotIn("discussion_messages", tables)
            self.assertIn("afisha", tables)
            self.assertIn("users", tables)
        await self.migrate("upgrade", "head")
        status, body = await self.request(
            "POST", body={"text": "After upgrade"}, token=self.token()
        )
        self.assertEqual(status, 201)
        self.assertEqual(body["text"], "After upgrade")


if __name__ == "__main__":
    unittest.main()
