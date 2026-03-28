"""equity overview foundation

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-28

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # ohlcv — add interval column
    # ------------------------------------------------------------------ #
    op.add_column(
        "ohlcv",
        sa.Column("interval", sa.String(5), nullable=False, server_default="1d"),
    )

    # Drop old PK and create new composite PK (time, ticker, interval)
    # op.execute is required since TimescaleDB does not support native Alembic PK modification
    op.execute("ALTER TABLE ohlcv DROP CONSTRAINT ohlcv_pkey")
    op.execute("ALTER TABLE ohlcv ADD PRIMARY KEY (time, ticker, interval)")

    # Drop old index, create new index including interval
    op.drop_index("ix_ohlcv_ticker_time", table_name="ohlcv")
    op.create_index("ix_ohlcv_ticker_time_interval", "ohlcv", ["ticker", "time", "interval"])

    # ------------------------------------------------------------------ #
    # fundamentals — add roe column
    # ------------------------------------------------------------------ #
    op.add_column(
        "fundamentals",
        sa.Column("roe", sa.Numeric(10, 4), nullable=True),
    )


def downgrade() -> None:
    # Reverse fundamentals roe
    op.drop_column("fundamentals", "roe")

    # Reverse ohlcv interval changes
    op.drop_index("ix_ohlcv_ticker_time_interval", table_name="ohlcv")
    op.create_index("ix_ohlcv_ticker_time", "ohlcv", ["ticker", "time"])
    op.execute("ALTER TABLE ohlcv DROP CONSTRAINT ohlcv_pkey")
    op.execute("ALTER TABLE ohlcv ADD PRIMARY KEY (time, ticker)")
    op.drop_column("ohlcv", "interval")
