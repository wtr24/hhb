"""ingestion hypertables

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-25

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # fundamentals — equity snapshot data (PE, EV/EBITDA, market cap, D/E)
    # ------------------------------------------------------------------ #
    op.create_table(
        "fundamentals",
        sa.Column("time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("pe_ratio", sa.Numeric(10, 4)),
        sa.Column("ev_ebitda", sa.Numeric(10, 4)),
        sa.Column("market_cap", sa.BigInteger()),
        sa.Column("debt_equity", sa.Numeric(10, 4)),
        sa.Column("source", sa.String(20)),
        sa.PrimaryKeyConstraint("time", "ticker"),
    )
    op.execute(
        "SELECT create_hypertable('fundamentals', 'time', if_not_exists => TRUE)"
    )
    op.create_index("ix_fundamentals_ticker_time", "fundamentals", ["ticker", "time"])

    # ------------------------------------------------------------------ #
    # macro_series — FRED / BLS time-series observations
    # ------------------------------------------------------------------ #
    op.create_table(
        "macro_series",
        sa.Column("time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("series_id", sa.String(30), nullable=False),
        sa.Column("value", sa.Numeric(18, 6)),
        sa.Column("source", sa.String(20), server_default="fred"),
        sa.PrimaryKeyConstraint("time", "series_id"),
    )
    op.execute(
        "SELECT create_hypertable('macro_series', 'time', if_not_exists => TRUE)"
    )
    op.create_index("ix_macro_series_id_time", "macro_series", ["series_id", "time"])

    # ------------------------------------------------------------------ #
    # fx_rates — Frankfurter currency pairs
    # ------------------------------------------------------------------ #
    op.create_table(
        "fx_rates",
        sa.Column("time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("base", sa.String(3), nullable=False),
        sa.Column("quote", sa.String(3), nullable=False),
        sa.Column("rate", sa.Numeric(18, 8), nullable=False),
        sa.Column("source", sa.String(20), server_default="frankfurter"),
        sa.PrimaryKeyConstraint("time", "base", "quote"),
    )
    op.execute(
        "SELECT create_hypertable('fx_rates', 'time', if_not_exists => TRUE)"
    )
    op.create_index("ix_fx_rates_pair_time", "fx_rates", ["base", "quote", "time"])

    # ------------------------------------------------------------------ #
    # yield_curve — US Treasury par yield curve (12 tenors)
    # ------------------------------------------------------------------ #
    op.create_table(
        "yield_curve",
        sa.Column("time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("bc_1month", sa.Numeric(8, 4)),
        sa.Column("bc_2month", sa.Numeric(8, 4)),
        sa.Column("bc_3month", sa.Numeric(8, 4)),
        sa.Column("bc_6month", sa.Numeric(8, 4)),
        sa.Column("bc_1year", sa.Numeric(8, 4)),
        sa.Column("bc_2year", sa.Numeric(8, 4)),
        sa.Column("bc_3year", sa.Numeric(8, 4)),
        sa.Column("bc_5year", sa.Numeric(8, 4)),
        sa.Column("bc_7year", sa.Numeric(8, 4)),
        sa.Column("bc_10year", sa.Numeric(8, 4)),
        sa.Column("bc_20year", sa.Numeric(8, 4)),
        sa.Column("bc_30year", sa.Numeric(8, 4)),
        sa.Column("source", sa.String(20), server_default="us_treasury"),
        sa.PrimaryKeyConstraint("time"),
    )
    op.execute(
        "SELECT create_hypertable('yield_curve', 'time', if_not_exists => TRUE)"
    )

    # ------------------------------------------------------------------ #
    # Compression policies — 7-day chunk interval, compress after 30 days
    # Covers all 5 hypertables (ohlcv from 0001 + 4 new ones)
    # ------------------------------------------------------------------ #
    op.execute(
        "SELECT add_compression_policy('ohlcv', INTERVAL '30 days', if_not_exists => TRUE)"
    )
    op.execute(
        "SELECT add_compression_policy('fundamentals', INTERVAL '30 days', if_not_exists => TRUE)"
    )
    op.execute(
        "SELECT add_compression_policy('macro_series', INTERVAL '30 days', if_not_exists => TRUE)"
    )
    op.execute(
        "SELECT add_compression_policy('fx_rates', INTERVAL '30 days', if_not_exists => TRUE)"
    )
    op.execute(
        "SELECT add_compression_policy('yield_curve', INTERVAL '30 days', if_not_exists => TRUE)"
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("yield_curve")
    op.drop_table("fx_rates")
    op.drop_table("macro_series")
    op.drop_table("fundamentals")
