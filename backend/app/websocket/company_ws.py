"""
WebSocket handler for company connections.
Route: /ws/company/{company_id}/delivery/{delivery_id}
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.delivery_request import DeliveryRequest
from app.redis_client import get_redis

logger = logging.getLogger(__name__)

router = APIRouter()

_POLL_INTERVAL = 2  # seconds between location/status polls


@router.websocket("/ws/company/{company_id}/delivery/{delivery_id}")
async def company_delivery_ws(websocket: WebSocket, company_id: str, delivery_id: str):
    # 1. Accept connection
    await websocket.accept()

    # 2. Validate JWT from query param ?token=...
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("role") != "company":
            raise JWTError("wrong role")
        token_subject = payload.get("sub")
    except JWTError:
        await websocket.close(code=1008)
        return

    # 3. Verify company_id matches token subject
    if str(token_subject) != str(company_id):
        await websocket.close(code=1008)
        return

    # 4. Verify delivery exists and belongs to company_id
    async with AsyncSessionLocal() as db:
        try:
            delivery_uuid = UUID(delivery_id)
            company_uuid = UUID(company_id)
        except ValueError:
            await websocket.close(code=1008)
            return

        result = await db.execute(
            select(DeliveryRequest).where(
                DeliveryRequest.id == delivery_uuid,
                DeliveryRequest.company_id == company_uuid,
            )
        )
        delivery = result.scalar_one_or_none()

        if delivery is None:
            await websocket.close(code=1008)
            return

        deliverer_id = str(delivery.deliverer_id) if delivery.deliverer_id else None
        last_known_status = delivery.status

        redis = await get_redis()

        try:
            # 5. Poll loop
            while True:
                await asyncio.sleep(_POLL_INTERVAL)

                # Re-fetch delivery to get latest status
                await db.refresh(delivery)
                current_status = delivery.status

                # Read deliverer location from Redis
                if deliverer_id:
                    location_data = await redis.hgetall(f"deliverer:location:{deliverer_id}")
                    if location_data:
                        try:
                            msg = {
                                "type": "location_update",
                                "lat": float(location_data["lat"]),
                                "lng": float(location_data["lng"]),
                                "timestamp": location_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                            }
                            await websocket.send_text(json.dumps(msg))
                        except (KeyError, ValueError) as exc:
                            logger.warning("Invalid location data in Redis: %s", exc)

                # Check for status change to picked_up or completed
                if current_status != last_known_status and current_status in ("picked_up", "completed"):
                    status_msg = {
                        "type": "delivery_status",
                        "status": current_status,
                    }
                    await websocket.send_text(json.dumps(status_msg))
                    last_known_status = current_status

                # Close connection when delivery is completed
                if current_status == "completed":
                    await websocket.close(code=1000)
                    return

        except WebSocketDisconnect:
            logger.info("Company WebSocket disconnected: company=%s delivery=%s", company_id, delivery_id)
        except Exception as exc:
            logger.exception("Unexpected error in company WebSocket: %s", exc)
            try:
                await websocket.close(code=1011)
            except Exception:
                pass
