from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

OUTBOX_DDL = """
CREATE TABLE IF NOT EXISTS outbox (
    id TEXT PRIMARY KEY,
    saga_id TEXT,
    exchange TEXT NOT NULL,
    routing_key TEXT NOT NULL,
    envelope TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP NULL
)
"""


@dataclass
class OutboxRow:
    id: str
    saga_id: str | None
    exchange: str
    routing_key: str
    envelope_json: str


async def enqueue_outbox(
    session: AsyncSession,
    *,
    exchange: str,
    routing_key: str,
    envelope_json: str,
    saga_id: str | None = None,
) -> str:
    outbox_id = str(uuid4())
    await session.execute(
        text(
            "INSERT INTO outbox (id, saga_id, exchange, routing_key, envelope) "
            "VALUES (:id, :saga_id, :ex, :rk, :env)"
        ),
        {
            "id": outbox_id,
            "saga_id": saga_id,
            "ex": exchange,
            "rk": routing_key,
            "env": envelope_json,
        },
    )
    return outbox_id


async def fetch_pending(session: AsyncSession, *, limit: int = 50) -> list[OutboxRow]:
    result = await session.execute(
        text(
            "SELECT id, saga_id, exchange, routing_key, envelope "
            "FROM outbox WHERE published_at IS NULL "
            "ORDER BY created_at ASC LIMIT :limit"
        ),
        {"limit": limit},
    )
    return [
        OutboxRow(id=r[0], saga_id=r[1], exchange=r[2], routing_key=r[3], envelope_json=r[4])
        for r in result.all()
    ]


async def mark_published(session: AsyncSession, *, outbox_id: str) -> None:
    await session.execute(
        text("UPDATE outbox SET published_at = CURRENT_TIMESTAMP WHERE id = :id"),
        {"id": outbox_id},
    )
