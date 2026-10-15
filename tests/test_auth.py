import asyncio
import json
import os
import unittest
from datetime import UTC, datetime, timedelta
from http.cookies import SimpleCookie
from unittest.mock import patch
from uuid import UUID, uuid4

from alembic import command
from alembic.config import Config
from jose import jwt
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.core.config import Settings, settings
from src.infrastructure.jwt import decode_token, hash_refresh_token
from src.main import app
from src.repositories.storage.postgres.db_helper import db_helper
from src.repositories.storage.postgres.user_repository import SQLAlchemyUserRepository
from src.repositories.storage.postgres.user_session_repository import (
    SQLAlchemyUserSessionRepository,
)
from src.usecase.auth.auth_service import AuthService, auth_service


@unittest.skipUnless(
    os.getenv("RUN_AUTH_DB_TESTS") == "1",
    "Set RUN_AUTH_DB_TESTS=1 for PostgreSQL tests",
)
class AuthTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        url = make_url(settings.database_url)
        self.name = "codex_auth_test_" + uuid4().hex
        self.admin = create_async_engine(url, isolation_level="AUTOCOMMIT")
        self.addAsyncCleanup(self.admin.dispose)
        async with self.admin.connect() as connection:
            await connection.execute(text(f'CREATE DATABASE "{self.name}"'))
        self.addAsyncCleanup(self.drop_database)
        self.engine = create_async_engine(url.set(database=self.name))
        self.addAsyncCleanup(self.engine.dispose)
        self.factory = async_sessionmaker(
            self.engine, expire_on_commit=False, autoflush=False
        )
        await self.migrate("20261014_05")
        self.legacy_id = uuid4()
        async with self.engine.begin() as connection:
            await connection.execute(
                text(
                    "INSERT INTO users (id, username, role, created_at) VALUES (:id, 'existing_user', 'user', now())"
                ),
                {"id": self.legacy_id},
            )
        await self.migrate("head")

        async def get_session():
            async with self.factory() as session:
                yield session

        app.dependency_overrides[db_helper.get_session] = get_session
        self.addCleanup(app.dependency_overrides.pop, db_helper.get_session)

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

    async def request(
        self,
        path,
        *,
        data=None,
        cookie=None,
        access=None,
        method="POST",
        csrf=True,
        origin=None,
        headers=None,
    ):
        request_headers = {"host": "test", "content-type": "application/json"}
        if csrf:
            request_headers["x-requested-with"] = "XMLHttpRequest"
        if cookie is not None:
            request_headers["cookie"] = "refresh_token=" + cookie
        if access is not None:
            request_headers["authorization"] = "Bearer " + access
        if origin is not None:
            request_headers["origin"] = origin
        request_headers.update(headers or {})
        messages = []
        sent = False

        async def receive():
            nonlocal sent
            if not sent:
                sent = True
                return {
                    "type": "http.request",
                    "body": json.dumps(data).encode() if data else b"",
                    "more_body": False,
                }
            await asyncio.Event().wait()

        async def send(message):
            messages.append(message)

        await app(
            {
                "type": "http",
                "asgi": {"version": "3.0"},
                "http_version": "1.1",
                "method": method,
                "scheme": "http",
                "path": "/api/auth/" + path,
                "raw_path": ("/api/auth/" + path).encode(),
                "root_path": "",
                "query_string": b"",
                "headers": [
                    (key.encode(), value.encode())
                    for key, value in request_headers.items()
                ],
                "client": ("127.0.0.1", 12345),
                "server": ("test", 80),
            },
            receive,
            send,
        )
        start = next(item for item in messages if item["type"] == "http.response.start")
        body = b"".join(
            item.get("body", b"")
            for item in messages
            if item["type"] == "http.response.body"
        )
        response_headers = {
            key.decode(): value.decode() for key, value in start["headers"]
        }
        payload = (
            json.loads(body)
            if body and "application/json" in response_headers.get("content-type", "")
            else None
        )
        return start["status"], payload, response_headers

    def cookie(self, headers):
        cookie = SimpleCookie()
        cookie.load(headers["set-cookie"])
        return cookie["refresh_token"]

    async def register(self):
        status, data, headers = await self.request(
            "register",
            data={
                "username": "  Alice_1  ",
                "password": "test-password",
                "role": "admin",
            },
        )
        self.assertEqual(status, 201)
        return data, self.cookie(headers).value, headers

    async def login(self):
        status, data, headers = await self.request(
            "login", data={"username": "ALICE_1", "password": "test-password"}
        )
        self.assertEqual(status, 200)
        return data, self.cookie(headers).value

    async def me_status(self, access):
        status, _, _ = await self.request("me", access=access, method="GET")
        return status

    async def test_registration_login_cookie_and_migration(self):
        with patch.object(settings, "auth_cookie_secure", True):
            data, refresh, headers = await self.register()
        self.assertEqual(
            set(data),
            {"id", "username", "role", "access_token", "token_type", "expires_in"},
        )
        self.assertEqual(data["username"], "alice_1")
        self.assertEqual(data["role"], "user")
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["expires_in"], settings.access_token_expire_minutes * 60)
        cookie = self.cookie(headers)
        self.assertTrue(cookie["httponly"])
        self.assertTrue(cookie["secure"])
        self.assertEqual(cookie["path"], "/api/auth")
        self.assertEqual(cookie["samesite"], settings.auth_cookie_samesite)
        self.assertEqual(cookie["domain"], "")
        self.assertGreater(int(cookie["max-age"]), 0)
        self.assertEqual(headers["cache-control"], "no-store")
        self.assertEqual(await self.me_status(data["access_token"]), 200)
        async with self.engine.connect() as connection:
            self.assertEqual(
                await connection.scalar(
                    text("SELECT count(*) FROM users WHERE id=:id"),
                    {"id": self.legacy_id},
                ),
                1,
            )
            self.assertEqual(
                await connection.scalar(
                    text("SELECT version_num FROM alembic_version")
                ),
                "20261015_01",
            )
            self.assertEqual(
                await connection.scalar(
                    text("SELECT refresh_token_hash FROM user_sessions")
                ),
                hash_refresh_token(refresh),
            )
        status, _, _ = await self.request(
            "register", data={"username": "alice_1", "password": "test-password"}
        )
        self.assertEqual(status, 409)
        status, _, _ = await self.request(
            "register", data={"username": "ab", "password": "short"}
        )
        self.assertEqual(status, 422)
        errors = []
        for username in ("alice_1", "missing_user", "existing_user"):
            status, error, _ = await self.request(
                "login", data={"username": username, "password": "wrong-password"}
            )
            self.assertEqual(status, 401)
            errors.append(error)
        self.assertEqual(errors[0], errors[1])
        self.assertEqual(errors[1], errors[2])
        with patch.object(settings, "auth_cookie_secure", False):
            status, _, headers = await self.request(
                "login", data={"username": "alice_1", "password": "test-password"}
            )
        self.assertEqual(status, 200)
        self.assertFalse(self.cookie(headers)["secure"])
        await self.migrate("20261014_05", downgrade=True)
        await self.migrate("head")
        async with self.engine.connect() as connection:
            self.assertEqual(
                await connection.scalar(text("SELECT count(*) FROM users")), 2
            )

    async def test_independent_sessions_rotation_and_logout(self):
        first, refresh, _ = await self.register()
        second, other_refresh = await self.login()
        self.assertNotEqual(
            decode_token(first["access_token"])["sid"],
            decode_token(second["access_token"])["sid"],
        )
        status, updated, headers = await self.request("refresh", cookie=refresh)
        self.assertEqual(status, 200)
        rotated = self.cookie(headers).value
        self.assertNotEqual(rotated, refresh)
        self.assertEqual(
            decode_token(rotated, "refresh")["exp"],
            decode_token(refresh, "refresh")["exp"],
        )
        self.assertEqual(await self.me_status(updated["access_token"]), 200)
        status, body, headers = await self.request("logout", cookie=rotated)
        self.assertEqual((status, body), (204, None))
        self.assertEqual(self.cookie(headers)["max-age"], "0")
        self.assertEqual(await self.me_status(first["access_token"]), 401)
        self.assertEqual(await self.me_status(updated["access_token"]), 401)
        self.assertEqual(await self.me_status(second["access_token"]), 200)
        status, _, _ = await self.request("refresh", cookie=rotated)
        self.assertEqual(status, 401)
        status, _, _ = await self.request("refresh", cookie=other_refresh)
        self.assertEqual(status, 200)
        for cookie in (None, "invalid", rotated):
            status, _, _ = await self.request("logout", cookie=cookie)
            self.assertEqual(status, 204)

    async def test_refresh_replay_and_concurrent_rotation(self):
        first, refresh, _ = await self.register()
        other, _ = await self.login()
        responses = await asyncio.wait_for(
            asyncio.gather(
                self.request("refresh", cookie=refresh),
                self.request("refresh", cookie=refresh),
            ),
            timeout=20,
        )
        self.assertEqual(sorted(response[0] for response in responses), [200, 401])
        self.assertEqual(await self.me_status(first["access_token"]), 401)
        self.assertEqual(await self.me_status(other["access_token"]), 200)
        successful = next(response for response in responses if response[0] == 200)
        self.assertEqual(await self.me_status(successful[1]["access_token"]), 401)
        status, _, headers = await self.request(
            "refresh", cookie=self.cookie(successful[2]).value
        )
        self.assertEqual(status, 401)
        self.assertEqual(self.cookie(headers)["max-age"], "0")

    async def test_invalid_tokens_expiry_and_current_role(self):
        data, refresh, _ = await self.register()
        access = data["access_token"]
        self.assertEqual(await self.me_status(refresh), 401)
        self.assertEqual(await self.me_status(None), 401)
        status, _, _ = await self.request("refresh", cookie=access)
        self.assertEqual(status, 401)
        payload = decode_token(access)
        invalid_payloads = [
            dict(payload, exp=0),
            dict(payload, sid="not-a-uuid"),
            dict(payload, sub=str(uuid4())),
        ]
        missing_exp = dict(payload)
        missing_exp.pop("exp")
        invalid_payloads.append(missing_exp)
        for invalid in invalid_payloads:
            token = jwt.encode(
                invalid, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
            )
            self.assertEqual(await self.me_status(token), 401)
        self.assertEqual(await self.me_status(access + "broken"), 401)
        self.assertEqual(await self.me_status(access), 200)
        async with self.engine.begin() as connection:
            await connection.execute(
                text("UPDATE users SET role='admin' WHERE id=:id"),
                {"id": UUID(data["id"])},
            )
        status, current, _ = await self.request("me", access=access, method="GET")
        self.assertEqual((status, current["role"]), (200, "admin"))
        async with self.engine.begin() as connection:
            await connection.execute(
                text("UPDATE user_sessions SET expires_at=:expires"),
                {"expires": datetime.now(UTC) - timedelta(seconds=1)},
            )
        self.assertEqual(await self.me_status(access), 401)
        status, _, _ = await self.request("refresh", cookie=refresh)
        self.assertEqual(status, 401)

    async def test_csrf_and_cors(self):
        for path in ("register", "login", "refresh", "logout"):
            for options in (
                {"csrf": False},
                {"origin": "https://attacker.invalid"},
                {"origin": "null"},
            ):
                status, _, headers = await self.request(
                    path,
                    data={"username": "alice_1", "password": "test-password"},
                    **options,
                )
                self.assertEqual(status, 403)
                self.assertNotIn("set-cookie", headers)
        status, _, _ = await self.request(
            "register",
            data={"username": "alice_1", "password": "test-password"},
            origin="http://test",
        )
        self.assertEqual(status, 201)
        status, _, headers = await self.request("refresh", origin="http://test")
        self.assertEqual(status, 401)
        self.assertEqual(self.cookie(headers)["max-age"], "0")
        status, _, headers = await self.request(
            "refresh",
            method="OPTIONS",
            origin="https://attacker.invalid",
            headers={
                "access-control-request-method": "POST",
                "access-control-request-headers": "x-requested-with",
            },
        )
        self.assertEqual(status, 400)
        self.assertNotIn("access-control-allow-origin", headers)
        with self.assertRaises(ValueError):
            Settings(AUTH_COOKIE_SECURE=False, AUTH_COOKIE_SAMESITE="none")
        with self.assertRaises(ValueError):
            Settings(CORS_ORIGINS=["*"])
        with self.assertRaises(ValueError):
            Settings(JWT_SECRET_KEY="")

    async def test_registration_race_and_atomic_rollback(self):
        class RacingRepository(SQLAlchemyUserRepository):
            def __init__(self):
                self.arrivals = 0
                self.ready = asyncio.Event()

            async def get_by_username(self, session, username):
                user = await super().get_by_username(session, username)
                if username == "race_user" and self.arrivals < 2:
                    self.arrivals += 1
                    if self.arrivals == 2:
                        self.ready.set()
                    await self.ready.wait()
                return user

        with patch.object(auth_service, "repo", RacingRepository()):
            responses = await asyncio.wait_for(
                asyncio.gather(
                    *[
                        self.request(
                            "register",
                            data={"username": "race_user", "password": "test-password"},
                        )
                        for _ in range(2)
                    ]
                ),
                timeout=20,
            )
        self.assertEqual(sorted(response[0] for response in responses), [201, 409])

        class FailingSessionRepository(SQLAlchemyUserSessionRepository):
            async def create_session(self, session, user_session):
                await super().create_session(session, user_session)
                raise RuntimeError("test rollback")

        service = AuthService(SQLAlchemyUserRepository(), FailingSessionRepository())
        async with self.factory() as session:
            with self.assertRaisesRegex(RuntimeError, "test rollback"):
                await service.create_user("rolled_back", "test-password", session)
        async with self.engine.connect() as connection:
            self.assertEqual(
                await connection.scalar(
                    text("SELECT count(*) FROM users WHERE username='rolled_back'")
                ),
                0,
            )
            self.assertEqual(
                await connection.scalar(text("SELECT count(*) FROM user_sessions")), 1
            )


if __name__ == "__main__":
    unittest.main()
