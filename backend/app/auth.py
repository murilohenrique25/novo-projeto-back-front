from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/deliverer/login")


def create_access_token(
    subject: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(hours=settings.jwt_expiration_hours)

    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------

async def get_current_deliverer(
    token: Annotated[str, Depends(_oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.models.deliverer import Deliverer  # local import to avoid circular deps

    payload = decode_token(token)
    if payload.get("role") != "deliverer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    deliverer_id = payload.get("sub")
    result = await db.execute(select(Deliverer).where(Deliverer.id == deliverer_id))
    deliverer = result.scalar_one_or_none()

    if deliverer is None or deliverer.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return deliverer


async def get_current_company(
    token: Annotated[str, Depends(_oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.models.company import Company  # local import to avoid circular deps

    payload = decode_token(token)
    if payload.get("role") != "company":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    company_id = payload.get("sub")
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()

    if company is None or company.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return company


async def get_current_admin(
    token: Annotated[str, Depends(_oauth2_scheme)],
):
    payload = decode_token(token)
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload
