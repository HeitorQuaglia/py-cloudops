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
        "resources",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("owner", sa.String, nullable=False),
        sa.Column("state", sa.String, nullable=False),
        sa.Column("aws_arn", sa.String),
        sa.Column("saga_id", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("type", "name", name="uq_resource_type_name"),
    )
    op.create_table(
        "name_reservations",
        sa.Column("name", sa.String, primary_key=True),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("reserved_by_saga", sa.String, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "processed_messages",
        sa.Column("message_id", sa.String, primary_key=True),
        sa.Column("handler", sa.String, primary_key=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("processed_messages")
    op.drop_table("name_reservations")
    op.drop_table("resources")
