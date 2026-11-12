import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.company import Company
from app.models.deliverer import Deliverer
from app.models.platform_settings import PlatformSettings

router = APIRouter(prefix="/admin", tags=["admin"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class DelivererOut(BaseModel):
    id: uuid.UUID
    full_name: str
    cpf: str
    email: str
    phone: str
    city_id: uuid.UUID
    reg_status: str
    rejection_reason: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RejectRequest(BaseModel):
    reason: str


class DelivererUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class CompanyOut(BaseModel):
    id: uuid.UUID
    cnpj: str
    legal_name: str
    trade_name: Optional[str]
    address: str
    phone: str
    email: str
    reg_status: str
    rejection_reason: Optional[str]
    is_deleted: bool
    balance: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class CompanyUpdate(BaseModel):
    legal_name: Optional[str] = None
    trade_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class SettingsOut(BaseModel):
    id: int
    platform_percentage: Decimal
    deliverer_percentage: Decimal
    updated_at: datetime

    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    platform_percentage: float
    deliverer_percentage: float


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _not_found(entity: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": "NOT_FOUND", "message": f"{entity} não encontrado(a)."},
    )


# ---------------------------------------------------------------------------
# Deliverers
# ---------------------------------------------------------------------------


@router.get("/deliverers", response_model=list[DelivererOut])
async def list_deliverers(
    reg_status: Optional[str] = Query(None),
    city_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    q = select(Deliverer).where(Deliverer.is_deleted == False)  # noqa: E712
    if reg_status:
        q = q.where(Deliverer.reg_status == reg_status)
    if city_id:
        q = q.where(Deliverer.city_id == city_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.patch("/deliverers/{id}/approve", response_model=DelivererOut)
async def approve_deliverer(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    result = await db.execute(
        select(Deliverer).where(Deliverer.id == id, Deliverer.is_deleted == False)  # noqa: E712
    )
    deliverer = result.scalar_one_or_none()
    if not deliverer:
        raise _not_found("Entregador")
    deliverer.reg_status = "approved"
    await db.flush()
    return deliverer


@router.patch("/deliverers/{id}/reject", response_model=DelivererOut)
async def reject_deliverer(
    id: uuid.UUID,
    body: RejectRequest,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    result = await db.execute(
        select(Deliverer).where(Deliverer.id == id, Deliverer.is_deleted == False)  # noqa: E712
    )
    deliverer = result.scalar_one_or_none()
    if not deliverer:
        raise _not_found("Entregador")
    deliverer.reg_status = "rejected"
    deliverer.rejection_reason = body.reason
    await db.flush()
    return deliverer


@router.put("/deliverers/{id}", response_model=DelivererOut)
async def update_deliverer(
    id: uuid.UUID,
    body: DelivererUpdate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    result = await db.execute(
        select(Deliverer).where(Deliverer.id == id, Deliverer.is_deleted == False)  # noqa: E712
    )
    deliverer = result.scalar_one_or_none()
    if not deliverer:
        raise _not_found("Entregador")
    data = body.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(deliverer, field, value)
    await db.flush()
    return deliverer


@router.delete("/deliverers/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deliverer(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    result = await db.execute(
        select(Deliverer).where(Deliverer.id == id, Deliverer.is_deleted == False)  # noqa: E712
    )
    deliverer = result.scalar_one_or_none()
    if not deliverer:
        raise _not_found("Entregador")
    deliverer.is_deleted = True
    await db.flush()


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------


@router.get("/companies", response_model=list[CompanyOut])
async def list_companies(
    reg_status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    q = select(Company).where(Company.is_deleted == False)  # noqa: E712
    if reg_status:
        q = q.where(Company.reg_status == reg_status)
    result = await db.execute(q)
    return result.scalars().all()


@router.patch("/companies/{id}/approve", response_model=CompanyOut)
async def approve_company(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    result = await db.execute(
        select(Company).where(Company.id == id, Company.is_deleted == False)  # noqa: E712
    )
    company = result.scalar_one_or_none()
    if not company:
        raise _not_found("Empresa")
    company.reg_status = "approved"
    await db.flush()
    return company


@router.patch("/companies/{id}/reject", response_model=CompanyOut)
async def reject_company(
    id: uuid.UUID,
    body: RejectRequest,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    result = await db.execute(
        select(Company).where(Company.id == id, Company.is_deleted == False)  # noqa: E712
    )
    company = result.scalar_one_or_none()
    if not company:
        raise _not_found("Empresa")
    company.reg_status = "rejected"
    company.rejection_reason = body.reason
    await db.flush()
    return company


@router.put("/companies/{id}", response_model=CompanyOut)
async def update_company(
    id: uuid.UUID,
    body: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    result = await db.execute(
        select(Company).where(Company.id == id, Company.is_deleted == False)  # noqa: E712
    )
    company = result.scalar_one_or_none()
    if not company:
        raise _not_found("Empresa")
    data = body.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(company, field, value)
    await db.flush()
    return company


@router.delete("/companies/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    result = await db.execute(
        select(Company).where(Company.id == id, Company.is_deleted == False)  # noqa: E712
    )
    company = result.scalar_one_or_none()
    if not company:
        raise _not_found("Empresa")
    company.is_deleted = True
    await db.flush()


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


@router.get("/settings", response_model=SettingsOut)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    result = await db.execute(select(PlatformSettings).where(PlatformSettings.id == 1))
    settings_row = result.scalar_one_or_none()
    if not settings_row:
        settings_row = PlatformSettings(id=1)
        db.add(settings_row)
        await db.flush()
    return settings_row


@router.put("/settings", response_model=SettingsOut)
async def update_settings(
    body: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    total = body.platform_percentage + body.deliverer_percentage
    if abs(total - 100.0) > 0.001:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "VALIDATION_ERROR",
                "message": "platform_percentage e deliverer_percentage devem somar 100.",
            },
        )

    result = await db.execute(select(PlatformSettings).where(PlatformSettings.id == 1))
    settings_row = result.scalar_one_or_none()
    if not settings_row:
        settings_row = PlatformSettings(id=1)
        db.add(settings_row)

    settings_row.platform_percentage = Decimal(str(body.platform_percentage))
    settings_row.deliverer_percentage = Decimal(str(body.deliverer_percentage))
    settings_row.updated_at = datetime.utcnow()
    await db.flush()
    return settings_row
