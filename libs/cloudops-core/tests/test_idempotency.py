import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from cloudops_core.idempotency import IDEMPOTENCY_DDL, claim_message


@pytest.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.execute(text(IDEMPOTENCY_DDL))
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


async def test_first_claim_returns_true(session):
    first = await claim_message(session, message_id="m-1", handler="catalog.validate")
    await session.commit()
    assert first is True


async def test_second_claim_returns_false(session):
    await claim_message(session, message_id="m-1", handler="catalog.validate")
    await session.commit()
    second = await claim_message(session, message_id="m-1", handler="catalog.validate")
    await session.commit()
    assert second is False


async def test_same_message_different_handler_is_independent(session):
    a = await claim_message(session, message_id="m-1", handler="handler-a")
    await session.commit()
    b = await claim_message(session, message_id="m-1", handler="handler-b")
    await session.commit()
    assert a is True
    assert b is True
