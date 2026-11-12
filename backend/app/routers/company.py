"""Company endpoints — balance inquiry, top-up (PIX and card), and deliveries."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_company
from app.database import get_db
from app.models.company import Company
from app.models.delivery_request import DeliveryRequest
from app.services.delivery import create_delivery_request
from app.services.payment import MockPaymentGateway, initiate_pix_topup, process_card_topup

router = APIRouter(prefix="/company", tags=["company"])

_gateway = MockPaymentGateway()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class BalanceResponse(BaseModel):
    balance: Decimal
    company_id: UUID


class PixTopupRequest(BaseModel):
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be greater than 0")
        return v


class PixTopupResponse(BaseModel):
    qr_code: str
    transaction_id: UUID


class CardTopupRequest(BaseModel):
    amount: Decimal
    card_token: str

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be greater than 0")
        return v


class CardTopupResponse(BaseModel):
    balance: Decimal
    transaction_id: UUID


class DeliveryCreateRequest(BaseModel):
    pickup_address: str
    pickup_lat: float
    pickup_lng: float
    destination_address: str
    destination_lat: float
    destination_lng: float
    city_id: UUID


class DeliveryCreateResponse(BaseModel):
    id: UUID
    status: str
    fee: Decimal
    platform_cut: Decimal
    deliverer_cut: Decimal
    radius_km: Decimal
    pickup_address: str
    destination_address: str
    city_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class DeliveryListItem(BaseModel):
    id: UUID
    status: str
    fee: Decimal
    pickup_address: str
    destination_address: str
    city_id: UUID
    created_at: datetime
    accepted_at: datetime | None
    picked_up_at: datetime | None
    completed_at: datetime | None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    company: Annotated[Company, Depends(get_current_company)],
):
    """Return the current balance for the authenticated company."""
    return BalanceResponse(balance=company.balance, company_id=company.id)


@router.post("/balance/topup/pix", response_model=PixTopupResponse)
async def topup_pix(
    body: PixTopupRequest,
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Initiate a PIX top-up and return the QR code."""
    result = await initiate_pix_topup(
        company_id=company.id,
        amount=body.amount,
        db=db,
        gateway=_gateway,
    )
    return PixTopupResponse(**result)


@router.post("/balance/topup/card", response_model=CardTopupResponse)
async def topup_card(
    body: CardTopupRequest,
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Charge a card and credit the company balance."""
    result = await process_card_topup(
        company_id=company.id,
        amount=body.amount,
        card_token=body.card_token,
        db=db,
        gateway=_gateway,
    )
    return CardTopupResponse(**result)


@router.post("/deliveries", response_model=DeliveryCreateResponse, status_code=201)
async def create_delivery(
    body: DeliveryCreateRequest,
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new delivery request for the authenticated company."""
    delivery = await create_delivery_request(
        company_id=company.id,
        city_id=body.city_id,
        pickup_address=body.pickup_address,
        pickup_lat=body.pickup_lat,
        pickup_lng=body.pickup_lng,
        destination_address=body.destination_address,
        destination_lat=body.destination_lat,
        destination_lng=body.destination_lng,
        db=db,
    )
    return DeliveryCreateResponse.model_validate(delivery)


@router.get("/deliveries", response_model=list[DeliveryListItem])
async def list_deliveries(
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = Query(default=None),
):
    """List delivery requests for the authenticated company, optionally filtered by status."""
    query = select(DeliveryRequest).where(DeliveryRequest.company_id == company.id)
    if status is not None:
        query = query.where(DeliveryRequest.status == status)
    query = query.order_by(DeliveryRequest.created_at.desc())
    result = await db.execute(query)
    deliveries = result.scalars().all()
    return [DeliveryListItem.model_validate(d) for d in deliveries]
