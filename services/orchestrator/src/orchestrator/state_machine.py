import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.models import Outbox, Saga, SagaStep
from orchestrator.saga_definitions import Step, get_saga_def


def _envelope_json(*, type_: str, payload: dict[str, Any], correlation_id: str,
                   causation_id: str | None) -> str:
    return json.dumps({
        "message_id": str(uuid4()),
        "correlation_id": correlation_id,
        "causation_id": causation_id,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "type": type_,
        "version": 1,
        "payload": payload,
    })


async def start_saga(
    session: AsyncSession, *, saga_type: str, payload: dict[str, Any]
) -> str:
    steps = get_saga_def(saga_type)
    saga = Saga(
        id=str(uuid4()),
        type=saga_type,
        state="RUNNING",
        current_step=0,
        payload=payload,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        version=1,
    )
    session.add(saga)
    await session.flush()

    for idx, step in enumerate(steps):
        session.add(
            SagaStep(saga_id=saga.id, step_id=idx, name=step.name, status="PENDING", attempt=0)
        )

    first = steps[0]
    await _enqueue_command(
        session, saga=saga, step_index=0, step=first
    )
    await session.flush()
    return saga.id


async def _enqueue_command(
    session: AsyncSession, *, saga: Saga, step_index: int, step: Step
) -> None:
    cmd_payload = dict(saga.payload)
    cmd_payload["step_id"] = step_index
    envelope_json = _envelope_json(
        type_=step.cmd,
        payload=cmd_payload,
        correlation_id=saga.id,
        causation_id=None,
    )
    session.add(
        Outbox(
            id=str(uuid4()),
            saga_id=saga.id,
            exchange="cloudops.commands",
            routing_key=step.cmd,
            envelope=envelope_json,
        )
    )
    step_row = await session.get(SagaStep, (saga.id, step_index))
    if step_row is not None:
        step_row.status = "EXECUTING"


async def advance_saga(
    session: AsyncSession,
    *,
    saga_id: str,
    event_type: str,
    payload_result: dict[str, Any] | None = None,
    payload_error: str | None = None,
) -> None:
    saga = await session.get(Saga, saga_id)
    if saga is None:
        return
    steps = get_saga_def(saga.type)
    current = steps[saga.current_step]

    if event_type == current.event_completed:
        step_row = await session.get(SagaStep, (saga.id, saga.current_step))
        if step_row is not None:
            step_row.status = "COMPLETED"
            step_row.executed_at = datetime.now(timezone.utc)

        if saga.current_step + 1 >= len(steps):
            saga.state = "COMPLETED"
            saga.updated_at = datetime.now(timezone.utc)
            saga.version += 1
            return

        saga.current_step += 1
        saga.updated_at = datetime.now(timezone.utc)
        saga.version += 1
        await _enqueue_command(session, saga=saga, step_index=saga.current_step, step=steps[saga.current_step])

    elif event_type == current.event_failed:
        step_row = await session.get(SagaStep, (saga.id, saga.current_step))
        if step_row is not None:
            step_row.status = "FAILED"
            step_row.error = payload_error
            step_row.executed_at = datetime.now(timezone.utc)
        saga.state = "FAILED"
        saga.updated_at = datetime.now(timezone.utc)
        saga.version += 1
