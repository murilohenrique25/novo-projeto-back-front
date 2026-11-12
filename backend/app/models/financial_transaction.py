import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"
    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('company','deliverer','platform')",
            name="ck_financial_transactions_entity_type",
        ),
        CheckConstraint(
            "status IN ('pending','confirmed','failed')",
            name="ck_financial_transactions_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gateway_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    delivery_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_requests.id", name="fk_financial_transactions_delivery"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )

    # Relationships
    delivery: Mapped["DeliveryRequest | None"] = relationship(
        back_populates="financial_transactions"
    )
