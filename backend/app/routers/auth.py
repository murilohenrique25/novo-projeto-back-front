from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, hash_password, verify_password
from app.config import settings
from app.database import get_db
from app.models.company import Company
from app.models.deliverer import Deliverer

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class DelivererRegisterRequest(BaseModel):
    full_name: str
    cpf: str
    phone: str
    email: EmailStr
    password: str
    city_id: UUID
    document_photo: str

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 11:
            raise ValueError("CPF must be exactly 11 digits")
        return v


class CompanyRegisterRequest(BaseModel):
    cnpj: str
    legal_name: str
    trade_name: str | None = None
    address: str
    phone: str
    email: EmailStr
    password: str

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 14:
            raise ValueError("CNPJ must be exactly 14 digits")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Error helpers
# ---------------------------------------------------------------------------

def _error(status_code: int, error_code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"error": error_code, "message": message},
    )


# ---------------------------------------------------------------------------
# Deliverer endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/deliverer/register",
    status_code=status.HTTP_201_CREATED,
    response_model=MessageResponse,
)
async def register_deliverer(
    body: DelivererRegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Check for duplicate CPF or email
    existing = await db.execute(
        select(Deliverer).where(
            (Deliverer.cpf == body.cpf) | (Deliverer.email == body.email)
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise _error(409, "DUPLICATE_DOCUMENT", "CPF or email already registered")

    deliverer = Deliverer(
        full_name=body.full_name,
        cpf=body.cpf,
        phone=body.phone,
        email=body.email,
        password_hash=hash_password(body.password),
        city_id=body.city_id,
        document_photo=body.document_photo,
        reg_status="pending",
    )
    db.add(deliverer)
    await db.flush()

    return {"message": "Registration submitted successfully. Awaiting approval."}


@router.post("/deliverer/login", response_model=TokenResponse)
async def login_deliverer(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Deliverer).where(Deliverer.email == body.email, Deliverer.is_deleted.is_(False))
    )
    deliverer = result.scalar_one_or_none()

    if deliverer is None or not verify_password(body.password, deliverer.password_hash):
        raise _error(401, "INVALID_CREDENTIALS", "Invalid email or password")

    if deliverer.reg_status != "approved":
        raise _error(403, "REGISTRATION_NOT_APPROVED", "Your registration has not been approved yet")

    token = create_access_token(subject=str(deliverer.id), role="deliverer")
    return {"access_token": token, "token_type": "bearer"}


# ---------------------------------------------------------------------------
# Company endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/company/register",
    status_code=status.HTTP_201_CREATED,
    response_model=MessageResponse,
)
async def register_company(
    body: CompanyRegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    existing = await db.execute(
        select(Company).where(
            (Company.cnpj == body.cnpj) | (Company.email == body.email)
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise _error(409, "DUPLICATE_DOCUMENT", "CNPJ or email already registered")

    company = Company(
        cnpj=body.cnpj,
        legal_name=body.legal_name,
        trade_name=body.trade_name,
        address=body.address,
        phone=body.phone,
        email=body.email,
        password_hash=hash_password(body.password),
        reg_status="pending",
    )
    db.add(company)
    await db.flush()

    return {"message": "Registration submitted successfully. Awaiting approval."}


@router.post("/company/login", response_model=TokenResponse)
async def login_company(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Company).where(Company.email == body.email, Company.is_deleted.is_(False))
    )
    company = result.scalar_one_or_none()

    if company is None or not verify_password(body.password, company.password_hash):
        raise _error(401, "INVALID_CREDENTIALS", "Invalid email or password")

    if company.reg_status != "approved":
        raise _error(403, "REGISTRATION_NOT_APPROVED", "Your registration has not been approved yet")

    token = create_access_token(subject=str(company.id), role="company")
    return {"access_token": token, "token_type": "bearer"}


# ---------------------------------------------------------------------------
# Admin endpoint
# ---------------------------------------------------------------------------

@router.post("/admin/login", response_model=TokenResponse)
async def login_admin(body: AdminLoginRequest):
    if body.email != settings.admin_email or body.password != settings.admin_password:
        raise _error(401, "INVALID_CREDENTIALS", "Invalid email or password")

    token = create_access_token(subject="admin", role="admin")
    return {"access_token": token, "token_type": "bearer"}
