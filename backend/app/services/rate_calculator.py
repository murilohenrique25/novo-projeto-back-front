from decimal import Decimal
from typing import Protocol, runtime_checkable
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery_rate import DeliveryRate


@runtime_checkable
class RateLike(Protocol):
    min_radius_km: Decimal
    max_radius_km: Decimal
    fee: Decimal


def select_rate(distance: float | Decimal, rates: list) -> Decimal:
    """
    Find the rate where min_radius_km <= distance <= max_radius_km.

    Raises HTTPException 422 with DISTANCE_OUT_OF_COVERAGE if no rate covers the distance.
    Returns the matching fee as Decimal.
    """
    d = Decimal(str(distance))
    for rate in rates:
        min_r = Decimal(str(rate.min_radius_km)) if not isinstance(rate.min_radius_km, Decimal) else rate.min_radius_km
        max_r = Decimal(str(rate.max_radius_km)) if not isinstance(rate.max_radius_km, Decimal) else rate.max_radius_km
        if min_r <= d <= max_r:
            return Decimal(str(rate.fee)) if not isinstance(rate.fee, Decimal) else rate.fee

    raise HTTPException(
        status_code=422,
        detail={
            "error": "DISTANCE_OUT_OF_COVERAGE",
            "message": "Distância fora da cobertura configurada para esta empresa",
        },
    )


async def get_fee_for_company(
    company_id: UUID,
    distance_km: float | Decimal,
    db: AsyncSession,
) -> Decimal:
    """
    Query delivery_rates for the company and return the fee for the given distance.

    Raises HTTPException 422 with DISTANCE_OUT_OF_COVERAGE if no rate covers the distance.
    """
    result = await db.execute(
        select(DeliveryRate).where(DeliveryRate.company_id == company_id)
    )
    rates = result.scalars().all()
    return select_rate(distance_km, rates)


async def calculate_fee(
    company_id: UUID,
    pickup_lat: float,
    pickup_lng: float,
    dest_lat: float,
    dest_lng: float,
    db: AsyncSession,
) -> tuple[Decimal, Decimal]:
    """
    Calculate the delivery fee for a given company and route.

    Returns a tuple of (fee, distance_km).
    Raises HTTPException 422 with DISTANCE_OUT_OF_COVERAGE if no matching rate is found.
    """
    from app.services.distance import haversine_km

    distance_km = Decimal(str(round(haversine_km(pickup_lat, pickup_lng, dest_lat, dest_lng), 6)))
    fee = await get_fee_for_company(company_id, distance_km, db)
    return fee, distance_km
