"""initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- cities ---
    op.create_table(
        "cities",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("state", sa.String(2), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("name", name="uq_cities_name"),
    )

    # --- deliverers ---
    op.create_table(
        "deliverers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("cpf", sa.String(11), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("document_photo", sa.Text, nullable=False),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "reg_status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "balance",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("cpf", name="uq_deliverers_cpf"),
        sa.UniqueConstraint("email", name="uq_deliverers_email"),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], name="fk_deliverers_city"),
        sa.CheckConstraint(
            "reg_status IN ('pending','approved','rejected')",
            name="ck_deliverers_reg_status",
        ),
    )
    op.create_index("idx_deliverers_city", "deliverers", ["city_id"])
    op.create_index("idx_deliverers_status", "deliverers", ["reg_status", "is_active"])

    # --- companies ---
    op.create_table(
        "companies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("cnpj", sa.String(14), nullable=False),
        sa.Column("legal_name", sa.String(200), nullable=False),
        sa.Column("trade_name", sa.String(200), nullable=True),
        sa.Column("address", sa.Text, nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column(
            "reg_status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "balance",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("cnpj", name="uq_companies_cnpj"),
        sa.UniqueConstraint("email", name="uq_companies_email"),
        sa.CheckConstraint(
            "reg_status IN ('pending','approved','rejected')",
            name="ck_companies_reg_status",
        ),
    )

    # --- platform_settings ---
    op.create_table(
        "platform_settings",
        sa.Column("id", sa.Integer, primary_key=True, server_default="1"),
        sa.Column(
            "platform_percentage",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="20.00",
        ),
        sa.Column(
            "deliverer_percentage",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="80.00",
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.CheckConstraint("id = 1", name="single_row"),
    )

    # --- delivery_rates ---
    op.create_table(
        "delivery_rates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("min_radius_km", sa.Numeric(8, 2), nullable=False),
        sa.Column("max_radius_km", sa.Numeric(8, 2), nullable=False),
        sa.Column("fee", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name="fk_delivery_rates_company"
        ),
        sa.UniqueConstraint(
            "company_id",
            "min_radius_km",
            "max_radius_km",
            name="no_overlap",
        ),
    )
    op.create_index("idx_rates_company", "delivery_rates", ["company_id"])

    # --- delivery_requests ---
    op.create_table(
        "delivery_requests",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deliverer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("pickup_address", sa.Text, nullable=False),
        sa.Column("pickup_lat", sa.Numeric(10, 7), nullable=False),
        sa.Column("pickup_lng", sa.Numeric(10, 7), nullable=False),
        sa.Column("destination_address", sa.Text, nullable=False),
        sa.Column("destination_lat", sa.Numeric(10, 7), nullable=False),
        sa.Column("destination_lng", sa.Numeric(10, 7), nullable=False),
        sa.Column("radius_km", sa.Numeric(8, 2), nullable=False),
        sa.Column("fee", sa.Numeric(10, 2), nullable=False),
        sa.Column("platform_cut", sa.Numeric(10, 2), nullable=False),
        sa.Column("deliverer_cut", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("accepted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("picked_up_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name="fk_delivery_requests_company"
        ),
        sa.ForeignKeyConstraint(
            ["city_id"], ["cities.id"], name="fk_delivery_requests_city"
        ),
        sa.ForeignKeyConstraint(
            ["deliverer_id"],
            ["deliverers.id"],
            name="fk_delivery_requests_deliverer",
        ),
        sa.CheckConstraint(
            "status IN ('pending','accepted','picked_up','completed','cancelled')",
            name="ck_delivery_requests_status",
        ),
    )
    op.create_index(
        "idx_delivery_city", "delivery_requests", ["city_id", "status"]
    )
    op.create_index("idx_delivery_company", "delivery_requests", ["company_id"])

    # --- financial_transactions ---
    op.create_table(
        "financial_transactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_method", sa.String(20), nullable=True),
        sa.Column("gateway_ref", sa.Text, nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("delivery_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["delivery_id"],
            ["delivery_requests.id"],
            name="fk_financial_transactions_delivery",
        ),
        sa.CheckConstraint(
            "entity_type IN ('company','deliverer','platform')",
            name="ck_financial_transactions_entity_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending','confirmed','failed')",
            name="ck_financial_transactions_status",
        ),
    )


def downgrade() -> None:
    op.drop_table("financial_transactions")
    op.drop_index("idx_delivery_company", table_name="delivery_requests")
    op.drop_index("idx_delivery_city", table_name="delivery_requests")
    op.drop_table("delivery_requests")
    op.drop_index("idx_rates_company", table_name="delivery_rates")
    op.drop_table("delivery_rates")
    op.drop_table("platform_settings")
    op.drop_table("companies")
    op.drop_index("idx_deliverers_status", table_name="deliverers")
    op.drop_index("idx_deliverers_city", table_name="deliverers")
    op.drop_table("deliverers")
    op.drop_table("cities")
