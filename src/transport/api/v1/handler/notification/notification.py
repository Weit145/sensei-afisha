from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends

from src.repositories.storage.models.connectioninfo import NotificationType
from src.usecase.notification_service import notification_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws")
async def notification_endpoint(
    websocket: WebSocket,
    user_ip: str = Query(...),
) -> None:
    connected = await notification_service.Connect(websocket, user_ip)
    if not connected:
        return
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "switch_afisha":
                afisha_id = int(data["afisha_id"])
                await notification_service.SwitchAfisha(user_ip, afisha_id)
            elif action == "leave_to_main_menu":
                await notification_service.SwitchAfisha(user_ip, -1)
            elif action == "ping":
                await websocket.send_json({"type":"pong"})
            else:
                logger.warning("Unknown WS action: %s from %s", action, user_ip)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: user_ip=%s", user_ip)
    except Exception:
        logger.exception("WS error for user_ip=%s", user_ip)
    finally:
        await notification_service.Disconnect(user_ip)

