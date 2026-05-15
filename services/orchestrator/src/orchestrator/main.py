import asyncio
import os

from cloudops_core.amqp import AmqpClient
from cloudops_core.idempotency import claim_message
from cloudops_core.logging import configure_logging, get_logger

from orchestrator.db import SessionMaker
from orchestrator.outbox_publisher import run_outbox_publisher
from orchestrator.state_machine import advance_saga, start_saga

AMQP_URL = os.getenv("AMQP_URL", "amqp://cloudops:cloudops_pw@rabbitmq:5672/")

log = get_logger()


async def on_reply(envelope_dict, headers):
    saga_id = envelope_dict["correlation_id"]
    message_id = envelope_dict["message_id"]
    type_ = envelope_dict["type"]
    payload = envelope_dict.get("payload") or {}

    async with SessionMaker() as session:
        first = await claim_message(session, message_id=message_id, handler="orchestrator.reply")
        if not first:
            await session.commit()
            return

        if type_.endswith(".completed"):
            await advance_saga(session, saga_id=saga_id, event_type=type_, payload_result=payload.get("result"))
        elif type_.endswith(".failed"):
            await advance_saga(session, saga_id=saga_id, event_type=type_, payload_error=payload.get("error"))
        await session.commit()

    log.info("advanced", saga_id=saga_id, event=type_)


async def on_operation_requested(envelope_dict, headers):
    message_id = envelope_dict["message_id"]
    payload = envelope_dict["payload"]
    saga_type = payload["operation"]
    op_payload = payload.get("parameters", {})

    async with SessionMaker() as session:
        first = await claim_message(session, message_id=message_id, handler="orchestrator.start")
        if not first:
            await session.commit()
            return
        saga_id = await start_saga(session, saga_type=saga_type, payload=op_payload)
        await session.commit()

    log.info("saga_started", saga_id=saga_id, type=saga_type)


async def main() -> None:
    configure_logging(service="orchestrator")
    amqp = AmqpClient(url=AMQP_URL)
    await amqp.connect()

    await amqp.declare_queue(
        "orchestrator.starts",
        exchange="cloudops.events",
        routing_key="evt.operation.requested",
    )

    log.info("starting", queues=["orchestrator.replies", "orchestrator.starts"])

    await asyncio.gather(
        amqp.consume("orchestrator.replies", on_reply),
        amqp.consume("orchestrator.starts", on_operation_requested),
        run_outbox_publisher(amqp),
    )


if __name__ == "__main__":
    asyncio.run(main())
