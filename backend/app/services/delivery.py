from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery_request import DeliveryRequest
from app.models.financial_transaction import FinancialTransaction
from app.models.platform_settings import PlatformSettings
from app.services.rate_calculator import calculate_fee


async def create_delivery_request(
    company_id: UUID,
    city_id: UUID,
    pickup_address: str,
    pickup_lat: float,
    pickup_lng: float,
    destination_address: str,
    destination_lat: float,
    destination_lng: float,
    db: AsyncSession,
) -> DeliveryRequest:
    """
    Create a delivery request for a company.

    Steps:
    1. Calculate distance and fee (raises 422 DISTANCE_OUT_OF_COVERAGE if no rate matches)
    2. Load platform_settings to get split percentages
    3. Atomically debit company balance (raises 422 INSUFFICIENT_BALANCE if balance < fee)
    4. Create DeliveryRequest with status='pending'
    5. Create FinancialTransaction for the debit
    """
    # 1. Calculate fee and distance via rate_calculator (also calls haversine_km internally)
    fee, distance_km = await calculate_fee(
        company_id=company_id,
        pickup_lat=pickup_lat,
        pickup_lng=pickup_lng,
        dest_lat=destination_lat,
        dest_lng=destination_lng,
        db=db,
    )

    # 2. Load platform settings (singleton row id=1)
    result = await db.execute(
        select(PlatformSettings).where(PlatformSettings.id == 1)
    )
    settings = result.scalar_one()

    platform_percentage = Decimal(str(settings.platform_percentage))
    deliverer_percentage = Decimal(str(settings.deliverer_percentage))

    # 3. Calculate cuts
    platform_cut = (fee * platform_percentage / Decimal("100")).quantize(Decimal("0.01"))
    deliverer_cut = (fee * deliverer_percentage / Decimal("100")).quantize(Decimal("0.01"))

    # 4. Atomically debit company balance
    update_result = await db.execute(
        text(
            "UPDATE companies SET balance = balance - :fee "
            "WHERE id = :id AND balance >= :fee"
        ),
        {"fee": fee, "id": company_id},
    )
    if update_result.rowcount == 0:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "INSUFFICIENT_BALANCE",
                "message": "Saldo insuficiente para criar a solicitação de entrega",
            },
        )

    # 5. Create DeliveryRequest
    delivery = DeliveryRequest(
        company_id=company_id,
        city_id=city_id,
        pickup_address=pickup_address,
        pickup_lat=Decimal(str(pickup_lat)),
        pickup_lng=Decimal(str(pickup_lng)),
        destination_address=destination_address,
        destination_lat=Decimal(str(destination_lat)),
        destination_lng=Decimal(str(destination_lng)),
        radius_km=distance_km,
        fee=fee,
        platform_cut=platform_cut,
        deliverer_cut=deliverer_cut,
        status="pending",
    )
    db.add(delivery)
    await db.flush()  # get delivery.id before creating the transaction

    # 6. Create FinancialTransaction for the debit
    transaction = FinancialTransaction(
        entity_type="company",
        entity_id=company_id,
        type="delivery_debit",
        amount=fee,
        status="confirmed",
        delivery_id=delivery.id,
    )
    db.add(transaction)

    return delivery
