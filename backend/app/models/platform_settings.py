from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Integer, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PlatformSettings(Base):
    __tablename__ = "platform_settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="single_row"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, server_default="1")
    platform_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default="20.00"
    )
    deliverer_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default="80.00"
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )
