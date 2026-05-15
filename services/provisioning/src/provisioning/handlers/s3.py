from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from provisioning.models import Execution


@dataclass
class HandlerReply:
    outcome: str
    result: dict[str, Any] | None = None
    error: str | None = None


async def handle_create_bucket(
    session: AsyncSession,
    *,
    payload: dict[str, Any],
    saga_id: str,
    step_id: str,
    s3_client,
) -> HandlerReply:
    name = payload["name"]
    execution = Execution(
        saga_id=saga_id,
        step_id=step_id,
        command="create_s3_bucket",
        status="EXECUTING",
    )
    session.add(execution)
    await session.flush()

    try:
        s3_client.create_bucket(Bucket=name)
    except Exception as exc:
        execution.status = "FAILED"
        execution.error = str(exc)
        return HandlerReply(outcome="failed", error=str(exc))

    arn = f"arn:aws:s3:::{name}"
    execution.status = "COMPLETED"
    execution.result_arn = arn
    return HandlerReply(outcome="completed", result={"arn": arn, "name": name})


# Stub para Iteração 2
async def handle_delete_bucket(
    session: AsyncSession,
    *,
    payload: dict[str, Any],
    saga_id: str,
    step_id: str,
    s3_client,
) -> HandlerReply:
    return HandlerReply(outcome="completed")
