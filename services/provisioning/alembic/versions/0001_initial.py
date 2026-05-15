"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-15
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "executions",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("saga_id", sa.String, nullable=False),
        sa.Column("step_id", sa.String, nullable=False),
        sa.Column("command", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False),
        sa.Column("result_arn", sa.String),
        sa.Column("error", sa.String),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "processed_messages",
        sa.Column("message_id", sa.String, primary_key=True),
        sa.Column("handler", sa.String, primary_key=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("processed_messages")
    op.drop_table("executions")
