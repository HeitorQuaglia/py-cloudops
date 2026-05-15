from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from cloudops_core.outbox import OUTBOX_DDL, OutboxRow, enqueue_outbox, fetch_pending, mark_published


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.execute(text(OUTBOX_DDL))
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


async def test_enqueue_then_fetch_returns_row(session):
    await enqueue_outbox(
        session,
        exchange="cloudops.commands",
        routing_key="cmd.catalog.validate",
        envelope_json='{"message_id":"m1","correlation_id":"saga-1","type":"cmd.catalog.validate","occurred_at":"2026-05-15T00:00:00+00:00","version":1,"payload":{}}',
        saga_id="saga-1",
    )
    await session.commit()

    rows = await fetch_pending(session, limit=10)
    assert len(rows) == 1
    assert rows[0].routing_key == "cmd.catalog.validate"


async def test_mark_published_removes_from_pending(session):
    await enqueue_outbox(
        session,
        exchange="cloudops.commands",
        routing_key="cmd.catalog.validate",
        envelope_json='{"message_id":"m1"}',
        saga_id="saga-1",
    )
    await session.commit()
    [row] = await fetch_pending(session, limit=10)

    await mark_published(session, outbox_id=row.id)
    await session.commit()

    rows = await fetch_pending(session, limit=10)
    assert rows == []
