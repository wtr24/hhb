"""ta engine — pattern stats and pivot points hypertables

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-29
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ta_pattern_stats — nightly candlestick pattern win rates + p-values (D-07)
    op.create_table(
        "ta_pattern_stats",
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("timeframe", sa.String(5), nullable=False),
        sa.Column("pattern_name", sa.String(50), nullable=False),
        sa.Column("n_occurrences", sa.Integer, nullable=False),
        sa.Column("n_wins", sa.Integer, nullable=False),
        sa.Column("win_rate", sa.Float, nullable=True),  # null if n < 30
        sa.Column("p_value", sa.Float, nullable=True),   # null if n < 30
        sa.Column("is_bullish", sa.Boolean, nullable=False),
    )
    # TimescaleDB hypertable — call immediately after create_table while empty (Pitfall 4)
    op.execute(
        "SELECT create_hypertable('ta_pattern_stats', 'time', if_not_exists => TRUE)"
    )
    op.create_index(
        "ix_ta_pattern_stats_ticker_timeframe_pattern",
        "ta_pattern_stats",
        ["ticker", "timeframe", "pattern_name"],
    )

    # pivot_points — nightly pre-computed pivot levels (TA-07)
    op.create_table(
        "pivot_points",
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("timeframe", sa.String(5), nullable=False),
        sa.Column("method", sa.String(20), nullable=False),  # standard|woodie|camarilla|fibonacci|demark
        sa.Column("pp", sa.Float, nullable=False),
        sa.Column("r1", sa.Float, nullable=True),
        sa.Column("r2", sa.Float, nullable=True),
        sa.Column("r3", sa.Float, nullable=True),
        sa.Column("s1", sa.Float, nullable=True),
        sa.Column("s2", sa.Float, nullable=True),
        sa.Column("s3", sa.Float, nullable=True),
    )
    op.execute(
        "SELECT create_hypertable('pivot_points', 'time', if_not_exists => TRUE)"
    )
    op.create_index(
        "ix_pivot_points_ticker_timeframe_method",
        "pivot_points",
        ["ticker", "timeframe", "method"],
    )


def downgrade() -> None:
    op.drop_table("pivot_points")
    op.drop_table("ta_pattern_stats")
