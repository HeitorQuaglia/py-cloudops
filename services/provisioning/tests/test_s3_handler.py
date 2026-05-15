from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from provisioning.handlers.s3 import handle_create_bucket, handle_delete_bucket
from provisioning.models import Base


@pytest.fixture
async def maker():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


async def test_create_bucket_calls_boto_and_records(maker):
    s3 = MagicMock()
    async with maker() as s:
        reply = await handle_create_bucket(
            s,
            payload={"name": "test-bucket", "region": "us-east-1"},
            saga_id="saga-1",
            step_id="3",
            s3_client=s3,
        )
        await s.commit()
        assert reply.outcome == "completed"
        assert reply.result["arn"] == "arn:aws:s3:::test-bucket"
        s3.create_bucket.assert_called_once_with(Bucket="test-bucket")


async def test_create_bucket_failure_records_error(maker):
    s3 = MagicMock()
    s3.create_bucket.side_effect = RuntimeError("boom")
    async with maker() as s:
        reply = await handle_create_bucket(
            s,
            payload={"name": "x", "region": "us-east-1"},
            saga_id="saga-1",
            step_id="3",
            s3_client=s3,
        )
        await s.commit()
        assert reply.outcome == "failed"
        assert "boom" in reply.error


async def test_delete_bucket_stub(maker):
    s3 = MagicMock()
    async with maker() as s:
        reply = await handle_delete_bucket(
            s,
            payload={"name": "x"},
            saga_id="saga-1",
            step_id="3",
            s3_client=s3,
        )
        assert reply.outcome == "completed"
