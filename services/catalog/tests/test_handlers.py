import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from catalog.handlers import (
    handle_register,
    handle_reserve_name,
    handle_validate,
)
from catalog.models import Base, NameReservation, Resource


@pytest.fixture
async def maker():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


async def test_validate_accepts_lowercase_name(maker):
    async with maker() as s:
        reply = await handle_validate(s, payload={"name": "my-bucket", "type": "s3-bucket"})
        assert reply.outcome == "completed"


async def test_validate_rejects_uppercase(maker):
    async with maker() as s:
        reply = await handle_validate(s, payload={"name": "MyBucket", "type": "s3-bucket"})
        assert reply.outcome == "failed"
        assert "lowercase" in reply.error


async def test_reserve_name_creates_reservation(maker):
    async with maker() as s:
        reply = await handle_reserve_name(
            s,
            payload={"name": "b1", "type": "s3-bucket"},
            saga_id="saga-1",
        )
        await s.commit()
        assert reply.outcome == "completed"
        rows = (await s.execute(NameReservation.__table__.select())).all()
        assert len(rows) == 1


async def test_reserve_name_conflict_fails(maker):
    async with maker() as s:
        await handle_reserve_name(s, payload={"name": "b1", "type": "s3-bucket"}, saga_id="saga-1")
        await s.commit()
    async with maker() as s:
        reply = await handle_reserve_name(
            s, payload={"name": "b1", "type": "s3-bucket"}, saga_id="saga-2"
        )
        assert reply.outcome == "failed"


async def test_register_inserts_resource(maker):
    async with maker() as s:
        reply = await handle_register(
            s,
            payload={
                "name": "b1",
                "type": "s3-bucket",
                "owner": "team-a",
                "aws_arn": "arn:aws:s3:::b1",
            },
            saga_id="saga-1",
        )
        await s.commit()
        assert reply.outcome == "completed"
        rows = (await s.execute(Resource.__table__.select())).all()
        assert len(rows) == 1
        assert rows[0]._mapping["state"] == "ACTIVE"
