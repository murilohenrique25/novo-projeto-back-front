"""Deliverer endpoints — status toggle, delivery history, pickup and completion."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_deliverer
from app.database import get_db
from app.models.deliverer import Deliverer
from app.models.delivery_request import DeliveryRequest
from app.models.financial_transaction import FinancialTransaction
from app.redis_client import get_redis
from app.services.notification import accept_delivery

router = APIRouter(prefix="/deliverer", tags=["deliverer"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class StatusUpdateRequest(BaseModel):
    status: str  # "active" | "inactive"


class StatusUpdateResponse(BaseModel):
    is_active: bool


class DeliveryItem(BaseModel):
    id: UUID
    status: str
Response)
async def update_status(
    body: StatusUpdateRequest,
    deliverer: Annotated[Deliverer, Depends(get_current_deliverer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Toggle deliverer active/inactive status and update Redis set."""
    if body.status not in ("active", "inactive"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="status must be 'active' or 'inactive'",
        )

    is_active = body.status == "active"
    deliverer.is_active = is_active
    db.add(deliverer)
    await db.flush()

    redis = await get_redis()
    redis_key = f"city:active_deliverers:{deliverer.city_id}"
    deliverer_id_str = str(deliverer.id)

    if is_active:
        await redis.sadd(redis_key, deliverer_id_str)
    else:
        await redis.srem(redis_key, deliverer_id_str)

    return StatusUpdateResponse(is_active=is_active)


@router.get("/deliveries", response_model=list[DeliveryItem])
async def list_deliveries(
    deliverer: Annotated[Deliverer, Depends(get_current_deliverer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return all deliveries assigned to the current deliverer, newest first."""
    query = (
        select(DeliveryRequest)
        .where(DeliveryRequest.deliverer_id == deliverer.id)
        .order_by(DeliveryRequest.created_at.desc())
    )
    result = await db.execute(query)
    deliveries = result.scalars().all()
    return [DeliveryItem.model_validate(d) for d in deliveries]


@router.post("/deliveries/{delivery_id}/pickup", response_model=DeliveryItem)
async def pickup_delivery(
    delivery_id: UUID,
    deliverer: Annotated[Deliverer, Depends(get_current_deliverer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark a delivery as picked up (status: accepted → picked_up)."""
    result = await db.execute(
        select(DeliveryRequest).where(
            DeliveryRequest.id == delivery_id,
            DeliveryRequest.deliverer_id == deliverer.id,
            DeliveryRequest.status == "accepted",
        )
    )
    delivery = result.scalar_one_or_none()

    if delivery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found or not in accepted status",
        )

    delivery.status = "picked_up"
    delivery.picked_up_at = datetime.now(timezone.utc)
    db.add(delivery)
    await db.flush()

    return DeliveryItem.model_validate(delivery)


@router.post("/deliveries/{delivery_id}/complete", response_model=DeliveryItem)
async def complete_delivery(
    delivery_id: UUID,
    deliverer: Annotated[Deliverer, Depends(get_current_deliverer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Complete a delivery, credit deliverer balance, and record financial transactions."""
    result = await db.execute(
        select(DeliveryRequest).where(
            DeliveryRequest.id == delivery_id,
            DeliveryRequest.deliverer_id == deliverer.id,
            DeliveryRequest.status == "picked_up",
        )
    )
    delivery = result.scalar_one_or_none()

    if delivery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found or not in picked_up status",
        )

    # Update delivery status
    delivery.status = "completed"
    delivery.completed_at = datetime.now(timezone.utc)
    db.add(delivery)

    # Credit deliverer balance
    deliverer.balance = Decimal(str(deliverer.balance)) + Decimal(str(delivery.deliverer_cut))
    db.add(deliverer)

    # Financial transaction: deliverer credit
    tx_deliverer = FinancialTransaction(
        entity_type="deliverer",
        entity_id=deliverer.id,
        type="deliverer_credit",
        amount=delivery.deliverer_cut,
        status="confirmed",
        delivery_id=delivery.id,
    )
    db.add(tx_deliverer)

    # Financial transaction: platform revenue
    tx_platform = FinancialTransaction(
        entity_type="platform",
        entity_id=delivery.company_id,
        type="platform_revenue",
        amount=delivery.platform_cut,
        status="confirmed",
        delivery_id=delivery.id,
    )
    db.add(tx_platform)

    await db.flush()

    return DeliveryItem.model_validate(delivery)


@router.post("/deliveries/{delivery_id}/accept", response_model=DeliveryItem)
async def accept_delivery_endpoint(
    delivery_id: UUID,
    deliverer: Annotated[Deliverer, Depends(get_current_deliverer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Atomically accept a delivery for the current deliverer."""
    redis = await get_redis()
    delivery = await accept_delivery(delivery_id, deliverer.id, db, redis)
    return DeliveryItem.model_validate(delivery)
