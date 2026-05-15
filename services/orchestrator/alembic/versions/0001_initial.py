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
        "sagas",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("state", sa.String, nullable=False),
        sa.Column("current_step", sa.Integer, nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
    )
    op.create_table(
        "saga_steps",
        sa.Column("saga_id", sa.String, primary_key=True),
        sa.Column("step_id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False),
        sa.Column("attempt", sa.Integer, nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True)),
        sa.Column("error", sa.String),
    )
    op.create_table(
        "processed_messages",
        sa.Column("message_id", sa.String, primary_key=True),
        sa.Column("handler", sa.String, primary_key=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "outbox",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("saga_id", sa.String),
        sa.Column("exchange", sa.String, nullable=False),
        sa.Column("routing_key", sa.String, nullable=False),
        sa.Column("envelope", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("outbox")
    op.drop_table("processed_messages")
    op.drop_table("saga_steps")
    op.drop_table("sagas")
