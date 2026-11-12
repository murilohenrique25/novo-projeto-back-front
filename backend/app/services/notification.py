"""
Notification service — distributes delivery_notification and delivery_cancelled
messages to deliverers via Redis Pub/Sub.
"""
import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deliverer import Deliverer
from app.models.delivery_request import DeliveryRequest

logger = logging.getLogger(__name__)

# TTL for the notified-deliverers list (5 minutes)
_NOTIFIED_TTL = 300


async def notify_active_deliverers(
    delivery: DeliveryRequest,
    db: AsyncSession,
    redis,
) -> list[str]:
    """
    Publish a delivery_notification to every active deliverer in the delivery's city.

    Returns the list of deliverer IDs that were notified.
    """
    city_key = f"city:active_deliverers:{delivery.city_id}"
    deliverer_ids: set[str] = await redis.smembers(city_key)

    if not deliverer_ids:
        return []

    message = json.dumps(
        {
            "type": "delivery_notification",
            "delivery_id": str(delivery.id),
            "pickup_address": delivery.pickup_address,
            "destination_address": delivery.destination_address,
            "fee": float(delivery.fee),
            "city_id": str(delivery.city_id),
        }
    )

    notified: list[str] = []
    for deliverer_id in deliverer_ids:
        channel = f"deliverer:notifications:{deliverer_id}"
        await redis.publish(channel, message)
        notified.append(deliverer_id)

    # Persist the notified list so we can send cancellations later
    notified_key = f"delivery:notified:{delivery.id}"
    await redis.set(notified_key, json.dumps(notified), ex=_NOTIFIED_TTL)

    logger.info(
        "Notified %d deliverer(s) for delivery %s", len(notified), delivery.id
    )
    return notified


async def accept_delivery(
    delivery_id: UUID,
    deliverer_id: UUID,
    db: AsyncSession,
    redis,
) -> DeliveryRequest:
    """
    Atomically accept a delivery for a deliverer.

    - Acquires a Redis lock to prevent double-acceptance.
    - Validates delivery status and city match.
    - Updates delivery in DB.
    - Sends delivery_cancelled to all other notified deliverers.
    """
    lock_key = f"delivery:lock:{delivery_id}"
    acquired = await redis.set(lock_key, str(deliverer_id), nx=True, ex=10)

    if not acquired:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "DELIVERY_ALREADY_TAKEN",
                "message": "Esta entrega já foi aceita por outro entregador",
            },
        )

    # Load delivery
    result = await db.execute(
        select(DeliveryRequest).where(DeliveryRequest.id == delivery_id)
    )
    delivery = result.scalar_one_or_none()

    if delivery is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": "Entrega não encontrada"},
        )

    if delivery.status != "pending":
        raise HTTPException(
            status_code=409,
            detail={
                "error": "DELIVERY_ALREADY_TAKEN",
                "message": "Esta entrega não está mais disponível",
            },
        )

    # Load deliverer to check city
    deliverer_result = await db.execute(
        select(Deliverer).where(Deliverer.id == deliverer_id)
    )
    deliverer = deliverer_result.scalar_one_or_none()

    if deliverer is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": "Entregador não encontrado"},
        )

    if str(deliverer.city_id) != str(delivery.city_id):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "CITY_MISMATCH",
                "message": "O entregador não pertence à cidade desta entrega",
            },
        )

    # Update delivery
    delivery.status = "accepted"
    delivery.deliverer_id = deliverer_id
    delivery.accepted_at = datetime.now(timezone.utc)
    await db.commit()

    # Notify other deliverers that the delivery was taken
    await send_delivery_cancelled(delivery_id, exclude_deliverer_id=deliverer_id, redis=redis)

    logger.info("Delivery %s accepted by deliverer %s", delivery_id, deliverer_id)
    return delivery


async def send_delivery_cancelled(
    delivery_id: UUID,
    exclude_deliverer_id: UUID,
    redis,
) -> None:
    """
    Publish delivery_cancelled to all deliverers that were notified about this
    delivery, except the one who accepted it.
    """
    notified_key = f"delivery:notified:{delivery_id}"
    raw = await redis.get(notified_key)

    if not raw:
        return

    notified: list[str] = json.loads(raw)
    exclude_str = str(exclude_deliverer_id)

    message = json.dumps(
        {
            "type": "delivery_cancelled",
            "delivery_id": str(delivery_id),
        }
    )

    for deliverer_id in notified:
        if deliverer_id == exclude_str:
            continue
        channel = f"deliverer:notifications:{deliverer_id}"
        await redis.publish(channel, message)

    logger.info(
        "Sent delivery_cancelled for delivery %s to %d deliverer(s)",
        delivery_id,
        sum(1 for d in notified if d != exclude_str),
    )
