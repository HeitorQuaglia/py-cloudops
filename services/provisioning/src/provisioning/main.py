import asyncio
import os
from typing import Any

from pydantic import BaseModel

from cloudops_core.amqp import AmqpClient
from cloudops_core.envelope import new_envelope
from cloudops_core.idempotency import claim_message
from cloudops_core.logging import configure_logging, get_logger
from provisioning.aws_client import s3_client as make_s3
from provisioning.db import SessionMaker
from provisioning.handlers.s3 import handle_create_bucket, handle_delete_bucket

AMQP_URL = os.getenv("AMQP_URL", "amqp://cloudops:cloudops_pw@rabbitmq:5672/")

ROUTING_TO_HANDLER = {
    "cmd.provisioning.create_s3_bucket": ("create_s3_bucket", handle_create_bucket),
    "cmd.provisioning.delete_s3_bucket": ("delete_s3_bucket", handle_delete_bucket),
}

log = get_logger()


class _ReplyPayload(BaseModel):
    result: dict[str, Any] | None = None
    error: str | None = None


async def dispatch(envelope_dict, headers, amqp: AmqpClient) -> None:
    type_ = envelope_dict["type"]
    saga_id = envelope_dict["correlation_id"]
    message_id = envelope_dict["message_id"]
    payload = envelope_dict.get("payload") or {}
    step_id = payload.get("step_id", "?")

    if type_ not in ROUTING_TO_HANDLER:
        log.warning("unknown_type", type=type_)
        return

    handler_name, handler = ROUTING_TO_HANDLER[type_]

    async with SessionMaker() as session:
        first = await claim_message(
            session, message_id=message_id, handler=f"provisioning.{handler_name}"
        )
        if not first:
            await session.commit()
            return

        s3 = make_s3()
        reply = await handler(
            session, payload=payload, saga_id=saga_id, step_id=str(step_id), s3_client=s3
        )
        await session.commit()

    event_type = f"evt.provisioning.{handler_name}.{reply.outcome}"
    out = new_envelope(
        type_=event_type,
        payload=_ReplyPayload(result=reply.result, error=reply.error),
        correlation_id=saga_id,
        causation_id=message_id,
    )
    await amqp.publish(exchange="cloudops.events", routing_key=event_type, envelope=out)
    log.info("processed", type=type_, outcome=reply.outcome, saga_id=saga_id)


async def main() -> None:
    configure_logging(service="provisioning")
    amqp = AmqpClient(url=AMQP_URL)
    await amqp.connect()

    async def handler(envelope_dict, headers):
        await dispatch(envelope_dict, headers, amqp)

    log.info("starting", queue="provisioning.commands")
    await amqp.consume("provisioning.commands", handler)


if __name__ == "__main__":
    asyncio.run(main())
