import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.company import Company
from app.models.delivery_rate import DeliveryRate

router = APIRouter(prefix="/admin", tags=["admin-rates"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class DeliveryRateCreate(BaseModel):
    min_radius_km: Decimal
    max_radius_km: Decimal
    fee: Decimal


class DeliveryRateUpdate(BaseModel):
    min_radius_km: Decimal | None = None
    max_radius_km: Decimal | None = None
    fee: Decimal | None = None


class DeliveryRateOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    min_radius_km: Decimal
    max_radius_km: Decimal
    fee: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _not_found(entity: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": "NOT_FOUND", "message": f"{entity} não encontrado(a)."},
    )


async def _get_company(id: uuid.UUID, db: AsyncSession) -> Company:
    result = await db.execute(
        select(Company).where(Company.id == id, Company.is_deleted == False)  # noqa: E712
    )
    company = result.scalar_one_or_none()
    if not company:
        raise _not_found("Empresa")
    return company


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/companies/{id}/rates", response_model=list[DeliveryRateOut])
async def list_rates(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin=Depends(get_current_admin),
):
    await _get_company(id, db)
    result = await db.execute(
        select(DeliveryRate).where(DeliveryRate.company_id == id)
    )
    return result.scalars().all()


@router.post(
    "/companies/{id}/rates",
    response_model=DeliveryRateOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_rate(
    id: uuid.UUID,
    body: DeliveryRateCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin=Depends(get_current_admin),
):
    await _get_company(id, db)

    rate = DeliveryRate(
        company_id=id,
        min_radius_km=body.min_radius_km,
        max_radius_km=body.max_radius_km,
        fee=body.fee,
    )
    db.add(rate)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "DUPLICATE_RATE",
                "message": "Já existe uma faixa com os mesmos raios para esta empresa.",
            },
        )
    return rate


@router.put("/companies/{id}/rates/{rate_id}", response_model=DeliveryRateOut)
async def update_rate(
    id: uuid.UUID,
    rate_id: uuid.UUID,
    body: DeliveryRateUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin=Depends(get_current_admin),
):
    await _get_company(id, db)

    result = await db.execute(
        select(DeliveryRate).where(
            DeliveryRate.id == rate_id, DeliveryRate.company_id == id
        )
    )
    rate = result.scalar_one_or_none()
    if not rate:
        raise _not_found("Taxa")

    data = body.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(rate, field, value)

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "DUPLICATE_RATE",
                "message": "Já existe uma faixa com os mesmos raios para esta empresa.",
            },
        )
    return rate


@router.delete(
    "/companies/{id}/rates/{rate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_rate(
    id: uuid.UUID,
    rate_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin=Depends(get_current_admin),
):
    await _get_company(id, db)

    result = await db.execute(
        select(DeliveryRate).where(
            DeliveryRate.id == rate_id, DeliveryRate.company_id == id
        )
    )
    rate = result.scalar_one_or_none()
    if not rate:
        raise _not_found("Taxa")

    await db.delete(rate)
    await db.flush()
