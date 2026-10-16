import logging
import uuid

from fastapi import WebSocket

from src.domain.notification import Notification
from src.repositories.storage.models.connectioninfo import (
    MAIN_MENU_ID,
    ConnectionInfo,
    NotificationType,
)
from src.repositories.storage.redis.notification_repository import (
    RedisNotificationRepository,
    redis_notification_repository,
)

logger = logging.getLogger("NotificationService")


class NotificationService:

    def __init__(self, repo: RedisNotificationRepository, server_id: int):
        self.repo = repo
        self.server_id = server_id

        # connection_id → WebSocket
        self.local: dict[str, WebSocket] = {}

        # connection_id → afisha_id (где юзер сейчас)
        self.current_afisha: dict[str, int] = {}

        # afisha_id → set[connection_id] (кто в афише сейчас)
        self.rooms: dict[int, set[str]] = {}

    async def Connect(self, ws: WebSocket, user_ip: str, n_type: NotificationType = NotificationType.MAIN_MENU) -> str | None:
        """
        Принимает WebSocket, генерирует UUID, регистрирует соединение.
        Возвращает connection_id при успехе, None при ошибке.
        """
        try:
            await ws.accept()
        except Exception:
            logger.exception("Failed to accept websocket for user_ip=%s", user_ip)
            return None

        connection_id = str(uuid.uuid4())          # ← генерация UUID

        self.local[connection_id] = ws
        self._enter_room(connection_id, MAIN_MENU_ID)

        await self.repo.save_notification(ConnectionInfo(
            connection_id=connection_id,
            user_ip=user_ip,
            server_id=self.server_id,
            n_type=n_type,
            afisha_id=MAIN_MENU_ID,
        ))

        # сообщаем клиенту его connection_id, чтобы он знал свой ID
        await ws.send_json({"type": "connected", "connection_id": connection_id})

        return connection_id

    async def Disconnect(self, connection_id: str) -> bool:
        existed = connection_id in self.local or connection_id in self.current_afisha
        self._leave_room(connection_id)
        self.local.pop(connection_id, None)
        await self.repo.drop_connection(connection_id)
        return existed

    async def CheckNotificationConnection(self, connection_id: str) -> bool:
        if connection_id in self.local:
            return True
        return await self.repo.connection_exists(connection_id)

    async def SwitchAfisha(self, connection_id: str, afisha_id: uuid) -> None:
        self._leave_room(connection_id)
        self._enter_room(connection_id, afisha_id)
        await self.repo.update_afisha_id(connection_id, afisha_id)

    async def Subscribe(self, connection_id: str, afisha_id: uuid) -> None:
        self.current_afisha[connection_id] = afisha_id
        self.rooms.setdefault(afisha_id, set()).add(connection_id)
        await self.repo.update_afisha_id(connection_id, afisha_id)

    async def Unsubscribe(self, connection_id: str) -> None:
        self._leave_room(connection_id)
        self._enter_room(connection_id, MAIN_MENU_ID)
        await self.repo.update_afisha_id(connection_id, MAIN_MENU_ID)

    async def SendAboutNewEvents(self, connection_id: str, text: str) -> None:
        """Собирает Notification о новом событии и шлёт конкретному соединению."""
        notification = Notification(
            n_type=NotificationType.MAIN_MENU,
            content=text,
        )
        payload = notification.model_dump_json()
        ws = self.local.get(connection_id)
        if ws is not None:
            await self._safe_send(ws, payload, connection_id)
            return
        info = await self.repo.load_connection(connection_id)
        if info is not None:
            await self.repo.publish_to_server(info.server_id, payload)

    async def SendAboutNewDescussionMessages(self, afisha_id: uuid, text: str) -> None:
        """Собирает Notification о новом сообщении в обсуждении и шлёт всем в комнате."""
        notification = Notification(
            n_type=NotificationType.DISCUSSION,
            content=  str(afisha_id )+ " " + str(text),
        )
        payload = notification.model_dump_json()
        connection_ids = list(self.rooms.get(afisha_id, set()))

        for connection_id in connection_ids:
            ws = self.local.get(connection_id)
            if ws is not None:
                await self._safe_send(ws, payload, connection_id)

    async def SendAboutNewFeedBack(self, afisha_id: uuid, text: str) -> None:
        """Собирает Notification об отзыве и шлёт всем в комнате."""
        notification = Notification(
            n_type=NotificationType.DISCUSSION,
            content=  str(afisha_id )+ " " + str(text),
        )
        payload = notification.model_dump_json()
        connection_ids = list(self.rooms.get(afisha_id, set()))

        for connection_id in connection_ids:
            ws = self.local.get(connection_id)
            if ws is not None:
                await self._safe_send(ws, payload, connection_id)

    def _enter_room(self, connection_id: str, afisha_id: uuid) -> None:
        """Добавляет connection_id в комнату afisha_id (RAM-индексы)."""
        self.current_afisha[connection_id] = afisha_id
        self.rooms.setdefault(afisha_id, set()).add(connection_id)

    def _leave_room(self, connection_id: str) -> None:
        """Убирает connection_id из его текущей комнаты (RAM-индексы)."""
        old = self.current_afisha.pop(connection_id, None)
        if old is None:
            return
        room = self.rooms.get(old)
        if room is not None:
            room.discard(connection_id)
            if not room:
                self.rooms.pop(old, None)

    async def _safe_send(self, ws: WebSocket, payload: str, connection_id: str) -> None:
        """Отправка с обработкой ошибок — чтобы один упавший сокет не рушил рассылку."""
        try:
            await ws.send_text(payload)
        except Exception:
            logger.exception("Failed to send to connection_id=%s", connection_id)
            
    async def SendToMainMenu(self, text: str) -> None:
        notification = Notification(
            n_type=NotificationType.DISCUSSION,
            content=  str(text),
        )
        payload = notification.model_dump_json()
        connection_ids = list(self.rooms.get(MAIN_MENU_ID, set()))

        for connection_id in connection_ids:
            ws = self.local.get(connection_id)
            if ws is not None:
                await self._safe_send(ws, payload, connection_id)

notification_service = NotificationService(redis_notification_repository, 0)