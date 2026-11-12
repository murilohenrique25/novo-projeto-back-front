import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DeliveryRate(Base):
    __tablename__ = "delivery_rates"
    __table_args__ = (
        UniqueConstraint("company_id", "min_radius_km", "max_radius_km", name="no_overlap"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", name="fk_delivery_rates_company"),
        nullable=False,
    )
    min_radius_km: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    max_radius_km: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="delivery_rates")
