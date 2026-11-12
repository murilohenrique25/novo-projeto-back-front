import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Deliverer(Base):
    __tablename__ = "deliverers"
    __table_args__ = (
        CheckConstraint(
            "reg_status IN ('pending','approved','rejected')",
            name="ck_deliverers_reg_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    cpf: Mapped[str] = mapped_column(String(11), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    document_photo: Mapped[str] = mapped_column(Text, nullable=False)
    city_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cities.id", name="fk_deliverers_city"), nullable=False
    )
    reg_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
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
    city: Mapped["City"] = relationship(back_populates="deliverers")
    delivery_requests: Mapped[list["DeliveryRequest"]] = relationship(back_populates="deliverer")
