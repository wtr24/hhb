"""Add tiktok_videos table

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tiktok_videos",
        sa.Column("video_id",    sa.String(30),                  primary_key=True),
        sa.Column("account",     sa.String(100),                 nullable=False),
        sa.Column("url",         sa.Text,                        nullable=False),
        sa.Column("title",       sa.Text,                        nullable=True),
        sa.Column("upload_date", sa.String(20),                  nullable=True),
        sa.Column("segments",    JSONB,                          nullable=True),
        sa.Column("full_text",   sa.Text,                        nullable=True),
        sa.Column("scraped_at",  sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"),               nullable=False),
        sa.Column("error",       sa.Text,                        nullable=True),
    )
    op.create_index("ix_tiktok_videos_account", "tiktok_videos", ["account"])
    op.create_index("ix_tiktok_videos_scraped_at", "tiktok_videos", ["scraped_at"])


def downgrade() -> None:
    op.drop_index("ix_tiktok_videos_scraped_at", table_name="tiktok_videos")
    op.drop_index("ix_tiktok_videos_account", table_name="tiktok_videos")
    op.drop_table("tiktok_videos")
