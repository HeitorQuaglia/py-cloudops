import json

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from orchestrator.models import Base, Outbox, Saga, SagaStep
from orchestrator.state_machine import advance_saga, start_saga


@pytest.fixture
async def maker():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


async def test_start_saga_creates_saga_and_first_outbox(maker):
    async with maker() as s:
        saga_id = await start_saga(
            s,
            saga_type="create_s3_bucket",
            payload={"name": "b1", "type": "s3-bucket", "owner": "team-a"},
        )
        await s.commit()

        sagas = (await s.execute(Saga.__table__.select())).all()
        outbox = (await s.execute(Outbox.__table__.select())).all()

    assert len(sagas) == 1
    assert sagas[0]._mapping["state"] == "RUNNING"
    assert sagas[0]._mapping["current_step"] == 0
    assert len(outbox) == 1
    env = json.loads(outbox[0]._mapping["envelope"])
    assert env["type"] == "cmd.catalog.validate"


async def test_advance_on_success_enqueues_next_step(maker):
    async with maker() as s:
        saga_id = await start_saga(
            s, saga_type="create_s3_bucket", payload={"name": "b1", "type": "s3-bucket"}
        )
        await s.commit()

    async with maker() as s:
        await advance_saga(
            s,
            saga_id=saga_id,
            event_type="evt.catalog.validate.completed",
            payload_result={"validated_name": "b1"},
        )
        await s.commit()

    async with maker() as s:
        outbox = (await s.execute(Outbox.__table__.select())).all()
        sagas = (await s.execute(Saga.__table__.select())).all()

    assert sagas[0]._mapping["current_step"] == 1
    next_cmd = json.loads(outbox[1]._mapping["envelope"])
    assert next_cmd["type"] == "cmd.catalog.reserve_name"


async def test_completion_after_last_step(maker):
    async with maker() as s:
        saga_id = await start_saga(s, saga_type="create_s3_bucket", payload={"name": "b1"})
        await s.commit()

    types_in_order = [
        "evt.catalog.validate.completed",
        "evt.catalog.reserve_name.completed",
        "evt.provisioning.create_s3_bucket.completed",
        "evt.catalog.register.completed",
    ]
    for t in types_in_order:
        async with maker() as s:
            await advance_saga(s, saga_id=saga_id, event_type=t, payload_result={})
            await s.commit()

    async with maker() as s:
        sagas = (await s.execute(Saga.__table__.select())).all()

    assert sagas[0]._mapping["state"] == "COMPLETED"


async def test_failure_marks_saga_failed_in_iteration_1(maker):
    """
    Iteração 1: na falha de qualquer passo, marca saga como FAILED.
    (Compensação ativa entra na Iteração 2.)
    """
    async with maker() as s:
        saga_id = await start_saga(s, saga_type="create_s3_bucket", payload={"name": "B1"})
        await s.commit()

    async with maker() as s:
        await advance_saga(
            s,
            saga_id=saga_id,
            event_type="evt.catalog.validate.failed",
            payload_error="bad name",
        )
        await s.commit()

    async with maker() as s:
        sagas = (await s.execute(Saga.__table__.select())).all()

    assert sagas[0]._mapping["state"] == "FAILED"
