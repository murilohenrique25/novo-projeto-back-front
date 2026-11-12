"""Payment service — PIX and card top-up flows.

Supports swappable gateway implementations via the PaymentGateway protocol.
"""

import asyncio
import uuid
from decimal import Decimal
from typing import Protocol

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.financial_transaction import FinancialTransaction


# ---------------------------------------------------------------------------
# Gateway protocol
# ---------------------------------------------------------------------------

class PaymentGateway(Protocol):
    async def create_pix(self, amount: Decimal, reference: str) -> dict:
        """Return {"qr_code": str, "gateway_ref": str}."""
        ...

    async def charge_card(self, amount: Decimal, card_token: str) -> dict:
        """Return {"approved": bool, "gateway_ref": str, "decline_reason": str | None}."""
        ...


# ---------------------------------------------------------------------------
# Mock implementation (dev / test)
# ---------------------------------------------------------------------------

class MockPaymentGateway:
    """Always succeeds — suitable for development and automated tests."""

    async def create_pix(self, amount: Decimal, reference: str) -> dict:
        return {
            "qr_code": f"00020126360014BR.GOV.BCB.PIX0114mock-{reference}",
            "gateway_ref": f"mock-pix-{reference}",
        }

    async def charge_card(self, amount: Decimal, card_token: str) -> dict:
        return {
            "approved": True,
            "gateway_ref": f"mock-card-{card_token[:8]}",
            "decline_reason": None,
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_RETRY_BACKOFFS = (1, 2, 4)  # seconds between attempts


async def _retry_gateway(coro_factory, attempts: int = 3):
    """Call *coro_factory()* up to *attempts* times with exponential backoff."""
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            return await coro_factory()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if i < attempts - 1:
                await asyncio.sleep(_RETRY_BACKOFFS[i])
    raise last_exc  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

async def initiate_pix_topup(
    company_id: uuid.UUID,
    amount: Decimal,
    db: AsyncSession,
    gateway: PaymentGateway,
) -> dict:
    """Create a pending PIX top-up transaction and return the QR code.

    Returns {"qr_code": str, "transaction_id": UUID}.
    """
    # 1. Persist the pending transaction first (req 9.7)
    txn = FinancialTransaction(
        entity_type="company",
        entity_id=company_id,
        type="topup_pix",
        amount=amount,
        payment_method="pix",
        status="pending",
    )
    db.add(txn)
    await db.flush()  # obtain txn.id without committing

    # 2. Call gateway with retry
    reference = str(txn.id)
    result = await _retry_gateway(
        lambda: gateway.create_pix(amount, reference)
    )

    # 3. Store gateway reference
    txn.gateway_ref = result["gateway_ref"]
    await db.flush()

    return {"qr_code": result["qr_code"], "transaction_id": txn.id}


async def process_card_topup(
    company_id: uuid.UUID,
    amount: Decimal,
    card_token: str,
    db: AsyncSession,
    gateway: PaymentGateway,
) -> dict:
    """Charge a card and, if approved, credit the company balance.

    Returns {"balance": Decimal, "transaction_id": UUID}.
    Raises HTTPException 422 PAYMENT_DECLINED on decline (no card data exposed).
    """
    # 1. Persist pending transaction (req 9.7)
    txn = FinancialTransaction(
        entity_type="company",
        entity_id=company_id,
        type="topup_card",
        amount=amount,
        payment_method="card",
        status="pending",
    )
    db.add(txn)
    await db.flush()

    # 2. Charge with retry
    result = await _retry_gateway(
        lambda: gateway.charge_card(amount, card_token)
    )

    txn.gateway_ref = result["gateway_ref"]

    if not result["approved"]:
        # Mark failed — do NOT expose card_token or decline_reason to caller (req 9.6)
        txn.status = "failed"
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "PAYMENT_DECLINED", "message": "Card payment was declined."},
        )

    # 3. Increment balance atomically and confirm transaction (req 9.4, 9.5)
    company_result = await db.execute(
        select(Company).where(Company.id == company_id).with_for_update()
    )
    company = company_result.scalar_one()
    company.balance += amount
    txn.status = "confirmed"
    await db.flush()

    return {"balance": company.balance, "transaction_id": txn.id}


async def confirm_pix_payment(
    gateway_ref: str,
    amount: Decimal,
    db: AsyncSession,
) -> None:
    """Webhook handler: confirm a pending PIX transaction and credit the company.

    Finds the FinancialTransaction by *gateway_ref*, increments the company
    balance by *amount*, and sets the transaction status to 'confirmed'.
    """
    txn_result = await db.execute(
        select(FinancialTransaction).where(
            FinancialTransaction.gateway_ref == gateway_ref,
            FinancialTransaction.status == "pending",
        )
    )
    txn = txn_result.scalar_one_or_none()
    if txn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Pending transaction not found."},
        )

    company_result = await db.execute(
        select(Company).where(Company.id == txn.entity_id).with_for_update()
    )
    company = company_result.scalar_one()
    company.balance += amount
    txn.status = "confirmed"
    await db.flush()
