import asyncio
from datetime import datetime, timezone

import aio_pika
from sqlalchemy import select

from cloudops_core.amqp import AmqpClient
from cloudops_core.logging import get_logger
from orchestrator.db import SessionMaker
from orchestrator.models import Outbox

log = get_logger()


async def run_outbox_publisher(amqp: AmqpClient, *, interval: float = 0.5) -> None:
    """Polling worker: lê outbox com published_at NULL e publica."""
    while True:
        try:
            await _publish_pending(amqp)
        except Exception:
            log.exception("outbox_publisher_failed")
        await asyncio.sleep(interval)


async def _publish_pending(amqp: AmqpClient) -> None:
    async with SessionMaker() as session:
        rows = (
            await session.execute(
                select(Outbox).where(Outbox.published_at.is_(None)).order_by(Outbox.created_at).limit(50)
            )
        ).scalars().all()

        for row in rows:
            assert amqp._channel is not None
            ex = await amqp._channel.get_exchange(row.exchange, ensure=True)
            msg = aio_pika.Message(
                body=row.envelope.encode("utf-8"),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await ex.publish(msg, routing_key=row.routing_key)
            row.published_at = datetime.now(timezone.utc)
        await session.commit()
