"""macro dashboard — gilt_curve and vix_term_structure hypertables

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # gilt_curve — BoE daily nominal zero-coupon spot curve (D-11, D-12, D-13)
    # No interval column — single-frequency daily series
    op.create_table(
        "gilt_curve",
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(20), nullable=False, server_default="boe"),
        sa.Column("tenor_6m", sa.Float, nullable=True),
        sa.Column("tenor_1y", sa.Float, nullable=True),
        sa.Column("tenor_2y", sa.Float, nullable=True),
        sa.Column("tenor_3y", sa.Float, nullable=True),
        sa.Column("tenor_5y", sa.Float, nullable=True),
        sa.Column("tenor_7y", sa.Float, nullable=True),
        sa.Column("tenor_10y", sa.Float, nullable=True),
        sa.Column("tenor_15y", sa.Float, nullable=True),
        sa.Column("tenor_20y", sa.Float, nullable=True),
        sa.Column("tenor_25y", sa.Float, nullable=True),
        sa.Column("tenor_30y", sa.Float, nullable=True),
    )
    # CRITICAL: call create_hypertable immediately after create_table while table is empty
    op.execute(
        "SELECT create_hypertable('gilt_curve', 'time', if_not_exists => TRUE)"
    )
    op.create_index(
        "ix_gilt_curve_time",
        "gilt_curve",
        ["time"],
    )

    # vix_term_structure — 15-minute VIX spot + VIX3M + VIX6M snapshots (D-18, D-19, D-20)
    # No interval column — single-frequency 15-minute series
    op.create_table(
        "vix_term_structure",
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("spot_vix", sa.Float, nullable=False),
        sa.Column("vix_3m", sa.Float, nullable=True),
        sa.Column("vix_6m", sa.Float, nullable=True),
        sa.Column("contango", sa.Boolean, nullable=True),
        sa.Column("regime", sa.String(20), nullable=True),  # LOW_VOL|NORMAL|ELEVATED|CRISIS
    )
    # CRITICAL: call create_hypertable immediately after create_table while table is empty
    op.execute(
        "SELECT create_hypertable('vix_term_structure', 'time', if_not_exists => TRUE)"
    )
    op.create_index(
        "ix_vix_term_structure_time",
        "vix_term_structure",
        ["time"],
    )


def downgrade() -> None:
    op.drop_table("vix_term_structure")
    op.drop_table("gilt_curve")
