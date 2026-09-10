"""esquema inicial: trucks, drivers, telemetry_readings, commands, trips, carta_porte_records

Revision ID: 0001
Revises:
Create Date: 2026-09-06

"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trucks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("plates", sa.String(), nullable=False, unique=True),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("capacity_kg", sa.Float(), nullable=True),
        sa.Column("security_state", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "drivers",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("license_number", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
    )

    op.create_table(
        "telemetry_readings",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("truck_id", sa.String(), sa.ForeignKey("trucks.id"), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("speed_kmh", sa.Float(), nullable=False),
        sa.Column("fuel_level_pct", sa.Float(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "commands",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("truck_id", sa.String(), sa.ForeignKey("trucks.id"), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("requested_at", sa.DateTime(), nullable=True),
        sa.Column("applied_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "trips",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("truck_id", sa.String(), sa.ForeignKey("trucks.id"), nullable=False),
        sa.Column("driver_id", sa.String(), sa.ForeignKey("drivers.id"), nullable=False),
        sa.Column("origin", sa.String(), nullable=False),
        sa.Column("destination", sa.String(), nullable=False),
        sa.Column("cargo_description", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "carta_porte_records",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("trip_id", sa.String(), sa.ForeignKey("trips.id"), nullable=False, unique=True),
        sa.Column("folio", sa.String(), nullable=False),
        sa.Column("merchandise_description", sa.String(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("transport_config", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("carta_porte_records")
    op.drop_table("trips")
    op.drop_table("commands")
    op.drop_table("telemetry_readings")
    op.drop_table("drivers")
    op.drop_table("trucks")
