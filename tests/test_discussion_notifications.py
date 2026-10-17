"""Discussion notification contract and WebSocket integration checks."""

import asyncio
import json
import os
import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

os.environ.setdefault("JWT_SECRET_KEY", "discussion-notifications-tests-only-secret")

import test_discussion_pagination as pagination_tests
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.discussion.message import Message
from src.domain.err import UnauthorizedError
from src.domain.user import UserRole
from src.infrastructure.jwt import create_token
from src.repositories.storage.models.connectioninfo import (
    MAIN_MENU_ID,
    ConnectionInfo,
    NotificationType,
)
from src.repositories.storage.redis.notification_repository import (
    RedisNotificationRepository,
)
from src.transport.api.v1.handler.discussion import message as message_handler
from src.transport.api.v1.handler.notification import notification as websocket_handler
from src.usecase.discussion.message_service import MessageService
from src.usecase.notification_service import NotificationService
from src.usecase.port.discussion.message_repositories import MessageRepository
from src.usecase.port.notifier import Notifier


class MessageNotificationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.repo = AsyncMock(spec=MessageRepository)
        self.repo.afisha_exists.return_value = True
        self.repo.author_exists.return_value = True
        self.message = Message(afisha_id=uuid4(), author_id=uuid4(), text="Привет")
        self.repo.create_message.return_value = self.message
        self.notifier = AsyncMock(spec=Notifier)
        self.session = AsyncMock(spec=AsyncSession)
        self.service = MessageService(self.repo, self.notifier)

    async def test_publishes_only_after_commit_with_saved_fields(self):
        async def publish(afisha_id, text, user_id, nickname):
            self.repo.commit.assert_awaited_once_with(self.session)
            self.assertEqual(
                (afisha_id, text, user_id, nickname),
                (
                    self.message.afisha_id,
                    self.message.text,
                    self.message.author_id,
                    "author",
                ),
            )

        self.notifier.SendAboutNewDescussionMessages.side_effect = publish
        result = await self.service.create_message(self.message, self.session, "author")
        self.assertEqual(result, self.message)
        self.notifier.SendAboutNewDescussionMessages.assert_awaited_once()

    async def test_failed_commit_does_not_publish(self):
        self.repo.commit.side_effect = RuntimeError("Database unavailable")
        with self.assertRaises(RuntimeError):
            await self.service.create_message(self.message, self.session, "author")
        self.notifier.SendAboutNewDescussionMessages.assert_not_awaited()

    async def test_rejected_author_does_not_publish(self):
        self.repo.author_exists.return_value = False
        with self.assertRaises(UnauthorizedError):
            await self.service.create_message(self.message, self.session, "author")
        self.notifier.SendAboutNewDescussionMessages.assert_not_awaited()

    async def test_publish_failure_keeps_successful_result(self):
        self.notifier.SendAboutNewDescussionMessages.side_effect = RuntimeError(
            "Socket failed"
        )
        with self.assertLogs("src.usecase.discussion.message_service", level="ERROR"):
            result = await self.service.create_message(self.message, self.session, "author")
        self.assertEqual(result, self.message)
        self.repo.commit.assert_awaited_once_with(self.session)
        self.session.rollback.assert_not_awaited()


class RedisConnectionTests(unittest.IsolatedAsyncioTestCase):
    async def test_injected_client_and_uuid_round_trip(self):
        client = AsyncMock()
        repo = RedisNotificationRepository(client)
        concert_id = uuid4()
        info = ConnectionInfo(
            connection_id=str(uuid4()),
            user_ip="127.0.0.1",
            server_id=0,
            n_type=NotificationType.DISCUSSION,
            afisha_id=concert_id,
        )
        await repo.save_notification(info)
        client.hset.assert_awaited_once()
        values = client.hset.await_args.kwargs["mapping"]
        self.assertEqual(values["afisha_id"], str(concert_id))
        client.hgetall.return_value = values
        self.assertEqual(await repo.load_connection(info.connection_id), info)
        values["afisha_id"] = str(MAIN_MENU_ID)
        self.assertEqual(
            (await repo.load_connection(info.connection_id)).afisha_id, MAIN_MENU_ID
        )


class NotificationConnectionTests(unittest.IsolatedAsyncioTestCase):
    async def test_failed_registration_removes_local_connection_and_closes_socket(self):
        repo = AsyncMock(spec=RedisNotificationRepository)
        repo.save_notification.side_effect = ConnectionError("Redis unavailable")
        repo.drop_connection.side_effect = ConnectionError("Redis unavailable")
        service = NotificationService(repo, 0)
        socket = AsyncMock()
        with self.assertLogs("NotificationService", level="ERROR"):
            result = await service.Connect(socket, "127.0.0.1")
        self.assertIsNone(result)
        self.assertEqual(service.local, {})
        self.assertEqual(service.rooms, {})
        self.assertEqual(service.current_afisha, {})
        socket.close.assert_awaited_once_with(code=1011)

    async def test_broken_socket_does_not_block_other_subscribers(self):
        repo = AsyncMock(spec=RedisNotificationRepository)
        service = NotificationService(repo, 0)
        broken, healthy = AsyncMock(), AsyncMock()
        concert_id = uuid4()
        first = await service.Connect(broken, "127.0.0.1")
        second = await service.Connect(healthy, "127.0.0.1")
        await service.Subscribe(first, concert_id)
        await service.Subscribe(second, concert_id)
        broken.send_text.side_effect = RuntimeError("Disconnected")
        with self.assertLogs("NotificationService", level="ERROR"):
            await service.SendAboutNewDescussionMessages(
                concert_id, "Hello", uuid4(), "author"
            )
        healthy.send_text.assert_awaited_once()
        self.assertNotIn(first, service.local)
        self.assertEqual(service.rooms[concert_id], {second})

    async def test_feedback_notification_includes_user_id_and_nickname(self):
        repo = AsyncMock(spec=RedisNotificationRepository)
        service = NotificationService(repo, 0)
        socket = AsyncMock()
        connection_id = await service.Connect(socket, "127.0.0.1")
        concert_id, author_id = uuid4(), uuid4()
        await service.Subscribe(connection_id, concert_id)

        await service.SendAboutNewFeedBack(
            concert_id, "Отличный концерт", author_id, "listener_1"
        )

        payload = json.loads(socket.send_text.await_args.args[0])
        self.assertEqual(payload["user_id"], str(author_id))
        self.assertEqual(payload["nickname"], "listener_1")
        self.assertEqual(payload["n_type"], 3)

    async def test_new_concert_has_main_menu_type_and_stays_out_of_concert_room(self):
        service = NotificationService(AsyncMock(spec=RedisNotificationRepository), 0)
        home, concert = AsyncMock(), AsyncMock()
        await service.Connect(home, "127.0.0.1")
        concert_connection = await service.Connect(concert, "127.0.0.1")
        await service.Subscribe(concert_connection, uuid4())
        await service.SendToMainMenu("Новая афиша")
        self.assertEqual(json.loads(home.send_text.await_args.args[0])["n_type"], 1)
        concert.send_text.assert_not_awaited()

    async def test_follow_count_reaches_home_and_concert_subscribers(self):
        service = NotificationService(AsyncMock(spec=RedisNotificationRepository), 0)
        home, concert = AsyncMock(), AsyncMock()
        await service.Connect(home, "127.0.0.1")
        concert_connection = await service.Connect(concert, "127.0.0.1")
        afisha_id = uuid4()
        await service.Subscribe(concert_connection, afisha_id)
        await service.SendFollowersUpdated(afisha_id, 2)
        for socket in (home, concert):
            self.assertEqual(json.loads(socket.send_text.await_args.args[0]), {
                "type": "followers_updated", "afisha_id": str(afisha_id),
                "followers_count": 2,
            })


class ASGISocket:
    """Exercise Starlette's real WebSocket handling through ASGI queues."""

    def __init__(self, app):
        self.app = app
        self.incoming = asyncio.Queue()
        self.outgoing = asyncio.Queue()
        self.task = None

    async def open(self):
        scope = {
            "type": "websocket",
            "asgi": {"version": "3.0", "spec_version": "2.4"},
            "http_version": "1.1",
            "scheme": "ws",
            "path": "/api/ws",
            "raw_path": b"/api/ws",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
            "subprotocols": [],
        }
        self.task = asyncio.create_task(
            self.app(scope, self.incoming.get, self.outgoing.put)
        )
        await self.incoming.put({"type": "websocket.connect"})
        accepted = await asyncio.wait_for(self.outgoing.get(), 2)
        if accepted["type"] != "websocket.accept":
            raise AssertionError(accepted)
        return await self.receive_json()

    async def send_json(self, data):
        await self.send_raw(json.dumps(data))

    async def send_raw(self, data):
        await self.incoming.put({"type": "websocket.receive", "text": data})

    async def receive_json(self):
        message = await asyncio.wait_for(self.outgoing.get(), 2)
        if message["type"] != "websocket.send":
            raise AssertionError(message)
        return json.loads(message["text"])

    async def subscribe(self, concert_id):
        await self.send_json({"action": "switch_afisha", "afisha_id": str(concert_id)})
        return await self.receive_json()

    async def close(self):
        if self.task is not None and not self.task.done():
            await self.incoming.put({"type": "websocket.disconnect", "code": 1000})
            await asyncio.wait_for(self.task, 2)


@unittest.skipUnless(
    pagination_tests.TEST_DATABASE_URL,
    "Set DISCUSSION_TEST_DATABASE_URL for PostgreSQL/WebSocket checks",
)
class DiscussionWebSocketTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.fixture = pagination_tests.PaginationPostgresTests()
        await self.fixture.asyncSetUp()
        self.addAsyncCleanup(self.fixture.cleanup)
        self.app = self.fixture.app
        self.app.include_router(websocket_handler.router, prefix="/api")
        self.repo = AsyncMock(spec=RedisNotificationRepository)
        self.notifier = NotificationService(self.repo, 0)
        for target, attribute in (
            (websocket_handler, "notification_service"),
            (message_handler.message_service, "notifier"),
        ):
            patcher = patch.object(target, attribute, self.notifier)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.token = create_token(
            self.fixture.author_id, UserRole.USER, self.fixture.session_id
        )

    async def socket(self):
        socket = ASGISocket(self.app)
        self.addAsyncCleanup(socket.close)
        connected = await socket.open()
        self.assertEqual(connected["type"], "connected")
        return socket

    async def post(self, text, afisha_id=None):
        return await self.fixture.request(
            method="POST", body={"text": text}, token=self.token, afisha_id=afisha_id
        )

    async def test_guests_receive_notification_and_can_read_committed_message(self):
        first, second = await self.socket(), await self.socket()
        for socket in (first, second):
            self.assertEqual(
                await socket.subscribe(self.fixture.afisha_id),
                {"type": "subscribed", "afisha_id": str(self.fixture.afisha_id)},
            )
        status, saved = await self.post("Привет всем")
        self.assertEqual(status, 201)
        expected = {
            "n_type": 2,
            "text": "Привет всем",
            "user_id": str(self.fixture.author_id),
            "nickname": "pagination-test",
        }
        self.assertEqual(await first.receive_json(), expected)
        self.assertEqual(await second.receive_json(), expected)
        _, history = await self.fixture.request()
        self.assertEqual(history["items"][0]["id"], saved["id"])
        self.assertEqual(saved["nickname"], "pagination-test")
        self.assertEqual(history["items"][0]["nickname"], "pagination-test")

    async def test_switch_unsubscribe_and_disconnect_isolate_rooms(self):
        socket = await self.socket()
        await socket.subscribe(self.fixture.afisha_id)
        await socket.subscribe(self.fixture.other_afisha_id)
        await self.post("Wrong room")
        await socket.send_json({"action": "ping"})
        self.assertEqual(await socket.receive_json(), {"type": "pong"})
        await self.post("Right room", self.fixture.other_afisha_id)
        self.assertEqual((await socket.receive_json())["text"], "Right room")
        await socket.send_json({"action": "leave_to_main_menu"})
        self.assertEqual(await socket.receive_json(), {"type": "unsubscribed"})
        await self.post("Unsubscribed", self.fixture.other_afisha_id)
        await socket.send_json({"action": "ping"})
        self.assertEqual(await socket.receive_json(), {"type": "pong"})
        await socket.close()
        self.assertEqual(self.notifier.local, {})
        self.assertEqual(self.notifier.rooms, {})
        self.repo.drop_connection.assert_awaited_once()

    async def test_invalid_frames_do_not_close_connection(self):
        socket = await self.socket()
        for payload in ([], {"action": "switch_afisha", "afisha_id": "not-a-uuid"}):
            await socket.send_json(payload)
            self.assertEqual((await socket.receive_json())["type"], "error")
        await socket.send_raw("{invalid-json")
        self.assertEqual((await socket.receive_json())["type"], "error")
        self.assertEqual(
            (await socket.subscribe(self.fixture.afisha_id))["type"], "subscribed"
        )

    async def test_failed_commit_emits_nothing_and_rolls_back(self):
        socket = await self.socket()
        await socket.subscribe(self.fixture.afisha_id)
        with (
            patch.object(
                message_handler.message_service.repo,
                "commit",
                new=AsyncMock(side_effect=RuntimeError),
            ),
            self.assertRaises(RuntimeError),
        ):
            await self.post("Not committed")
        await socket.send_json({"action": "ping"})
        self.assertEqual(await socket.receive_json(), {"type": "pong"})
        _, history = await self.fixture.request()
        self.assertEqual(history["items"], [])

    async def test_notification_failure_does_not_fail_post(self):
        with (
            patch.object(
                self.notifier,
                "SendAboutNewDescussionMessages",
                new=AsyncMock(side_effect=RuntimeError("Notification failed")),
            ),
            self.assertLogs("src.usecase.discussion.message_service", level="ERROR"),
        ):
            status, saved = await self.post("Committed without notification")
        self.assertEqual(status, 201)
        _, history = await self.fixture.request()
        self.assertEqual(history["items"][0]["id"], saved["id"])


if __name__ == "__main__":
    unittest.main()
