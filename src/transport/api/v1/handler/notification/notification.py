import json
import logging
import uuid

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from src.usecase.notification_service import notification_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def notification_endpoint(
    websocket: WebSocket,
    user_ip: str | None = Query(None),
) -> None:
    client_ip = user_ip or (websocket.client.host if websocket.client else "unknown")
    connection_id = await notification_service.Connect(websocket, client_ip)
    if connection_id is None:
        return

    try:
        while True:
            try:
                data = await websocket.receive_json()
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue
            if not isinstance(data, dict):
                await websocket.send_json(
                    {"type": "error", "message": "Expected an object"}
                )
                continue
            action = data.get("action")

            if action == "switch_afisha":
                try:
                    afisha_id = uuid.UUID(str(data.get("afisha_id")))
                except ValueError:
                    await websocket.send_json(
                        {"type": "error", "message": "Invalid concert UUID"}
                    )
                    continue
                await notification_service.SwitchAfisha(connection_id, afisha_id)
                await websocket.send_json(
                    {"type": "subscribed", "afisha_id": str(afisha_id)}
                )
            elif action == "leave_to_main_menu":
                await notification_service.Unsubscribe(connection_id)
                await websocket.send_json({"type": "unsubscribed"})
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                logger.warning(
                    "Unknown WS action: %s from conn=%s", action, connection_id
                )

    except WebSocketDisconnect:
        logger.info(
            "WebSocket disconnected: connection_id=%s, user_ip=%s",
            connection_id,
            user_ip,
        )
    except Exception:
        logger.exception("WS error for connection_id=%s", connection_id)
    finally:
        await notification_service.Disconnect(connection_id)
