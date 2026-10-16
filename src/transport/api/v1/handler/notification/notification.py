import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from src.usecase.notification_service import notification_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def notification_endpoint(
    websocket: WebSocket,
    user_ip: str = Query(...),
) -> None:
    connection_id = await notification_service.Connect(websocket, user_ip)
    if connection_id is None:
        return

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "switch_afisha":
                afisha_id = int(data["afisha_id"])
                await notification_service.SwitchAfisha(connection_id, afisha_id)
            elif action == "leave_to_main_menu":
                await notification_service.SwitchAfisha(connection_id, -1)
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                logger.warning("Unknown WS action: %s from conn=%s", action, connection_id)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: connection_id=%s, user_ip=%s", connection_id, user_ip)
    except Exception:
        logger.exception("WS error for connection_id=%s", connection_id)
    finally:
        await notification_service.Disconnect(connection_id)