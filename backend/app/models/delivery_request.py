import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DeliveryRequest(Base):
    __tablename__ = "delivery_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','accepted','picked_up','completed','cancelled')",
            name="ck_delivery_requests_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", name="fk_delivery_requests_company"),
        nullable=False,
    )
    city_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cities.id", name="fk_delivery_requests_city"),
        nullable=False,
    )
    deliverer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deliverers.id", name="fk_delivery_requests_deliverer"),
        nullable=True,
    )
    pickup_address: Mapped[str] = mapped_column(Text, nullable=False)
    pickup_lat: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    pickup_lng: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    destination_address: Mapped[str] = mapped_column(Text, nullable=False)
    destination_lat: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    destination_lng: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    radius_km: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    platform_cut: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    deliverer_cut: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    accepted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    picked_up_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="delivery_requests")
    city: Mapped["City"] = relationship(back_populates="delivery_requests")
    deliverer: Mapped["Deliverer | None"] = relationship(back_populates="delivery_requests")
    financial_transactions: Mapped[list["FinancialTransaction"]] = relationship(
        back_populates="delivery"
    )
