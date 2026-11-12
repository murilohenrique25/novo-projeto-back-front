"""Webhook endpoints — called by external payment gateways (no auth required)."""

from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.payment import confirm_pix_payment

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class PaymentWebhookPayload(BaseModel):
    gateway_ref: str
    amount: Decimal
    event: str


@router.post("/payment", status_code=200)
async def payment_webhook(
    payload: PaymentWebhookPayload,
    db: AsyncSession = Depends(get_db),
):
    """Receive payment gateway notifications.

    Only processes ``event == "payment.confirmed"`` (PIX confirmation).
    Returns 404 if the matching pending transaction is not found.
    """
    if payload.event == "payment.confirmed":
        await confirm_pix_payment(payload.gateway_ref, payload.amount, db)

    return {"status": "ok"}
