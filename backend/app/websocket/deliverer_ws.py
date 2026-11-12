"""
WebSocket handler for deliverer connections.
Route: /ws/deliverer/{deliverer_id}
"""
import asyncio
import json
import logging
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.deliverer import Deliverer
from app.redis_client import get_redis

logger = logging.getLogger(__name__)

router = APIRouter()

# Heartbeat timeout in seconds — disconnect if no message received within this window
_HEARTBEAT_TIMEOUT = 35


async def mark_deliverer_inactive(deliverer_id: str, db: AsyncSession, redis) -> None:
    """Set deliverer as inactive, remove from city active set, delete location key."""
    result = await db.execute(select(Deliverer).where(Deliverer.id == deliverer_id))
    deliverer = result.scalar_one_or_none()
    if deliverer is None:
        return

    deliverer.is_active = False
    await db.commit()

    city_id = str(deliverer.city_id)
    await redis.srem(f"city:active_deliverers:{city_id}", deliverer_id)
    await redis.delete(f"deliverer:location:{deliverer_id}")
    await redis.delete(f"deliverer:ws_connected:{deliverer_id}")


async def _pubsub_listener(websocket: WebSocket, deliverer_id: str, redis) -> None:
    """
    Background task: subscribe to the deliverer's notification channel and
    forward every published message to the WebSocket client.
    """
    channel = f"deliverer:notifications:{deliverer_id}"
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])
    except Exception:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()


@router.websocket("/ws/deliverer/{deliverer_id}")
async def deliverer_ws(websocket: WebSocket, deliverer_id: str):
    # 1. Accept connection
    await websocket.accept()

    # 2. Validate JWT from query param ?token=...
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("role") != "deliverer":
            raise JWTError("wrong role")
        token_subject = payload.get("sub")
    except JWTError:
        await websocket.close(code=1008)
        return

    # 3. Load deliverer from DB; disconnect if not found or not approved
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Deliverer).where(Deliverer.id == deliverer_id))
        deliverer = result.scalar_one_or_none()

        if deliverer is None or deliverer.is_deleted:
            await websocket.close(code=1008)
            return

        if deliverer.reg_status != "approved":
            await websocket.close(code=1008)
            return

        # Ensure the token subject matches the deliverer_id path param
        if str(token_subject) != str(deliverer.id):
            await websocket.close(code=1008)
            return

        redis = await get_redis()
        city_id = str(deliverer.city_id)

        # Start background task that forwards Pub/Sub messages to the WebSocket
        listener_task = asyncio.create_task(
            _pubsub_listener(websocket, deliverer_id, redis)
        )

        try:
            while True:
                # 6. Heartbeat: 35s timeout on receive
                try:
                    raw = await asyncio.wait_for(websocket.receive_text(), timeout=_HEARTBEAT_TIMEOUT)
                except asyncio.TimeoutError:
                    # No message within timeout — mark inactive and close
                    await mark_deliverer_inactive(deliverer_id, db, redis)
                    await websocket.close(code=1000)
                    return

                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                msg_type = msg.get("type")

                if msg_type == "location_update":
                    # 4. Store location in Redis with TTL 35s
                    lat = msg.get("lat")
                    lng = msg.get("lng")
                    timestamp = msg.get("timestamp", "")

                    if lat is not None and lng is not None:
                        location_key = f"deliverer:location:{deliverer_id}"
                        await redis.hset(location_key, mapping={
                            "lat": str(lat),
                            "lng": str(lng),
                            "timestamp": timestamp,
                        })
                        await redis.expire(location_key, _HEARTBEAT_TIMEOUT)

                        # Renew ws_connected key
                        ws_key = f"deliverer:ws_connected:{deliverer_id}"
                        await redis.set(ws_key, "1", ex=_HEARTBEAT_TIMEOUT)

                elif msg_type == "status_change":
                    # 5. Update is_active in DB and manage city active set
                    status = msg.get("status")
                    if status == "active":
                        deliverer.is_active = True
                        await db.commit()
                        await redis.sadd(f"city:active_deliverers:{city_id}", deliverer_id)
                    elif status == "inactive":
                        deliverer.is_active = False
                        await db.commit()
                        await redis.srem(f"city:active_deliverers:{city_id}", deliverer_id)

        except WebSocketDisconnect:
            await mark_deliverer_inactive(deliverer_id, db, redis)
        except Exception as exc:
            logger.exception("Unexpected error in deliverer WebSocket: %s", exc)
            await mark_deliverer_inactive(deliverer_id, db, redis)
            await websocket.close(code=1011)
        finally:
            listener_task.cancel()
            try:
                await listener_task
            except asyncio.CancelledError:
                pass
