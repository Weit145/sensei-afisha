# тут реализация всех функций 
import logging
from src.domain.notification import Notification
from src.repositories.storage.redis.notification_repository import RedisNotificationRepository, redis_notification_repository
from src.repositories.storage.models.connectioninfo import (
    ConnectionInfo,
    NotificationType,
    MAIN_MENU_ID,
)

from fastapi import WebSocket

logger = logging.getLogger("NotificaionService")

MAIN_MENU_ID = -1

class NotificationService: 
    def __init__(self, repo: RedisNotificationRepository, server_id: int):
        self.repo = repo
        self.server_id = server_id

        # user_ip → WebSocket (живой сокет в этом процессе)
        self.local: dict[str, WebSocket] = {}

        # user_ip → afisha_id (где юзер сейчас) — зеркало Redis для скорости
        self.current_afisha: dict[str, int] = {}

        # afisha_id → set[user_id] (кто в афише сейчас)
        self.rooms: dict[int, set[str]] = {}

    async def Connect(self, ws: WebSocket, user_ip: str,)->bool:
        try:
            await websocket.accept()
        except Exception:
            logger.exception("Failed to accept websocket for user_ip=%s", user_ip)
            return False

        self.local[user_ip] = websocket
        self._enter_room(user_ip, MAIN_MENU_ID)

        await self.repo.save_notification(ConnectionInfo(
        user_ip=user_ip, 
        server_id=self.server_id, 
        n_type=n_type, 
        afisha_id=MAIN_MENU_ID))

        return True


    async def Disconnect(self, user_ip: str)->bool:
        existed = user_ip in self.local or user_ip in self.current_afisha
        self._leave_room(user_ip)
        self.local.pop(user_ip, None)
        await self.repo.drop_connection(user_ip)
        return existed

    async def CheckNotificationConnection(self, user_ip: str)->bool:
        if user_ip in self.local:
            return True
        return self.repo.connection_exists(user_ip)
        
    async def SwitchAfisha(self, user_ip: str, afisha_id: int) -> None:
        self._leave_room(user_ip)
        self._enter_room(user_ip, afisha_id )
        await self.repo.update_afisha_id(user_ip, afisha_id)
        
    async def Subscribe(self, user_ip: str, afisha_id: int) -> None:
        self.current_afisha[user_ip] = afisha_id
        self.rooms.setdefault(afisha_id, set()).add(user_ip)
        await self.repo.update_afisha_id(user_ip, afisha_id)

    async def Unsubscribe(self, user_ip: str) -> None:
        self._leave_room(user_ip)
        self._enter_room(user_ip, MAIN_MENU_ID)
        await self.repo.update_afisha_id(user_ip, MAIN_MENU_ID)

    async def SendAboutNewEvents(self, user_ip: str, notification: Notification) -> None:
        payload = notification.model_dump_json()
        ws = self.local.get(user_ip)
        if ws is not None:
            await self._safe_send(ws, payload, user_ip)
            return 
        info = await self.repo.load_connection(user_ip)
        if info is not None:
            await self.repo.publish_to_server(info.server_id, payload)

    async def SendAboutNewDescussionMessages(self, afisha_id: int, notification: Notification) -> None:
        payload = notification.model_dump_json()
        user_ips = list(self.rooms.get(afisha_id, set()))

        for user_ip in user_ips:
            ws = self.local.get(user_ip)
            if ws is not None:
                await self._safe_send(ws, payload, user_ip)

    async def SendAboutNewFeedBack( self, afisha_id: int, notification: Notification) -> None:
        await self.SendAboutNewDescussionMessages(afisha_id, notification)
        
    def _enter_room(self, user_ip: str, afisha_id: int) -> None:
        """Добавляет user_ip в комнату afisha_id (RAM-индексы)."""
        self.current_room[user_ip] = afisha_id
        self.rooms.setdefault(afisha_id, set()).add(user_ip)

    def _leave_room(self, user_ip: str) -> None:
        """Убирает user_ip из его текущей комнаты (RAM-индексы)."""
        old = self.current_room.pop(user_ip, None)
        if old is None:
            return
        room = self.rooms.get(old)
        if room is not None:
            room.discard(user_ip)
            if not room:
                self.rooms.pop(old, None)

    async def _safe_send(self, ws: WebSocket, payload: str, user_ip: str) -> None:
        """Отправка с обработкой ошибок — чтобы один упавший сокет не рушил рассылку."""
        try:
            await ws.send_text(payload)
        except Exception:
            logger.exception("Failed to send to user_ip=%s", user_ip)

notification_service = NotificationService(redis_notification_repository, 0)