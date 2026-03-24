"""initial hypertables

Revision ID: 0001
Revises:
Create Date: 2026-03-24

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create base ohlcv table
    op.create_table(
        "ohlcv",
        sa.Column("time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("open", sa.Numeric(18, 6)),
        sa.Column("high", sa.Numeric(18, 6)),
        sa.Column("low", sa.Numeric(18, 6)),
        sa.Column("close", sa.Numeric(18, 6)),
        sa.Column("volume", sa.BigInteger()),
        sa.Column("source", sa.String(20)),
        sa.PrimaryKeyConstraint("time", "ticker"),
    )

    # Convert to TimescaleDB hypertable — must be called before any data is inserted
    op.execute(
        "SELECT create_hypertable('ohlcv', 'time', if_not_exists => TRUE)"
    )

    # Composite index for efficient per-ticker time-range queries
    op.create_index("ix_ohlcv_ticker_time", "ohlcv", ["ticker", "time"])


def downgrade() -> None:
    op.drop_table("ohlcv")
