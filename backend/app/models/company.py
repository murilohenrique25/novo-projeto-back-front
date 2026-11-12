import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        CheckConstraint(
            "reg_status IN ('pending','approved','rejected')",
            name="ck_companies_reg_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    cnpj: Mapped[str] = mapped_column(String(14), nullable=False, unique=True)
    legal_name: Mapped[str] = mapped_column(String(200), nullable=False)
    trade_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    reg_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )

    # Relationships
    delivery_rates: Mapped[list["DeliveryRate"]] = relationship(back_populates="company")
    delivery_requests: Mapped[list["DeliveryRequest"]] = relationship(back_populates="company")
