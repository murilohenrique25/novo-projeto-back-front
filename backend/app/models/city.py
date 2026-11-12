import uuid
from datetime import datetime

from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class City(Base):
    __tablename__ = "cities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )

    # Relationships
    deliverers: Mapped[list["Deliverer"]] = relationship(back_populates="city")
    delivery_requests: Mapped[list["DeliveryRequest"]] = relationship(back_populates="city")
