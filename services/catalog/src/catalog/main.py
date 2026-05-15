import asyncio
import os
from typing import Any

from pydantic import BaseModel

from catalog.db import SessionMaker
from catalog.handlers import (
    HandlerReply,
    handle_deregister,
    handle_register,
    handle_release_name,
    handle_reserve_name,
    handle_validate,
)
from cloudops_core.amqp import AmqpClient
from cloudops_core.envelope import new_envelope
from cloudops_core.idempotency import claim_message
from cloudops_core.logging import configure_logging, get_logger

AMQP_URL = os.getenv("AMQP_URL", "amqp://cloudops:cloudops_pw@rabbitmq:5672/")

ROUTING_TO_HANDLER = {
    "cmd.catalog.validate":      ("validate",      handle_validate,      False),
    "cmd.catalog.reserve_name":  ("reserve_name",  handle_reserve_name,  True),
    "cmd.catalog.register":      ("register",      handle_register,      True),
    "cmd.catalog.release_name":  ("release_name",  handle_release_name,  True),
    "cmd.catalog.deregister":    ("deregister",    handle_deregister,    True),
}

log = get_logger()


class _ReplyPayload(BaseModel):
    result: dict[str, Any] | None = None
    error: str | None = None


async def dispatch(envelope_dict: dict[str, Any], headers: dict[str, Any], amqp: AmqpClient) -> None:
    type_ = envelope_dict["type"]
    saga_id = envelope_dict["correlation_id"]
    message_id = envelope_dict["message_id"]
    payload = envelope_dict.get("payload") or {}

    if type_ not in ROUTING_TO_HANDLER:
        log.warning("unknown_type", type=type_)
        return

    handler_name, handler, needs_saga_id = ROUTING_TO_HANDLER[type_]

    async with SessionMaker() as session:
        first_time = await claim_message(session, message_id=message_id, handler=f"catalog.{handler_name}")
        if not first_time:
            log.info("duplicate", message_id=message_id, handler=handler_name)
            await session.commit()
            return

        if needs_saga_id:
            reply: HandlerReply = await handler(session, payload=payload, saga_id=saga_id)
        else:
            reply = await handler(session, payload=payload)

        await session.commit()

    event_type = f"evt.catalog.{handler_name}.{reply.outcome}"
    out = new_envelope(
        type_=event_type,
        payload=_ReplyPayload(result=reply.result, error=reply.error),
        correlation_id=saga_id,
        causation_id=message_id,
    )
    await amqp.publish(exchange="cloudops.events", routing_key=event_type, envelope=out)
    log.info("processed", type=type_, outcome=reply.outcome, saga_id=saga_id)


async def main() -> None:
    configure_logging(service="catalog")
    amqp = AmqpClient(url=AMQP_URL)
    await amqp.connect()

    async def handler(envelope_dict, headers):
        await dispatch(envelope_dict, headers, amqp)

    log.info("starting", queue="catalog.commands")
    await amqp.consume("catalog.commands", handler)


if __name__ == "__main__":
    asyncio.run(main())
