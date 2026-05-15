import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import aio_pika
from aio_pika.abc import AbstractIncomingMessage, AbstractRobustConnection

from cloudops_core.envelope import Envelope

log = logging.getLogger(__name__)

Handler = Callable[[dict[str, Any], dict[str, Any]], Awaitable[None]]


class AmqpClient:
    def __init__(self, *, url: str) -> None:
        self._url = url
        self._conn: AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractRobustChannel | None = None

    async def connect(self) -> None:
        self._conn = await aio_pika.connect_robust(self._url)
        self._channel = await self._conn.channel()
        await self._channel.set_qos(prefetch_count=10)

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()

    async def declare_queue(
        self, name: str, *, exchange: str, routing_key: str
    ) -> aio_pika.abc.AbstractRobustQueue:
        assert self._channel is not None
        queue = await self._channel.declare_queue(name, durable=True)
        ex = await self._channel.get_exchange(exchange, ensure=True)
        await queue.bind(ex, routing_key=routing_key)
        return queue

    async def publish(
        self,
        *,
        exchange: str,
        routing_key: str,
        envelope: Envelope,
        headers: dict[str, str] | None = None,
    ) -> None:
        assert self._channel is not None
        ex = await self._channel.get_exchange(exchange, ensure=True)
        body = envelope.model_dump_json().encode("utf-8")
        msg = aio_pika.Message(
            body=body,
            content_type="application/json",
            message_id=envelope.message_id,
            correlation_id=envelope.correlation_id,
            headers=headers or {},
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await ex.publish(msg, routing_key=routing_key)

    async def consume(self, queue_name: str, handler: Handler) -> None:
        assert self._channel is not None
        queue = await self._channel.get_queue(queue_name, ensure=True)

        async def _on_message(message: AbstractIncomingMessage) -> None:
            async with message.process(requeue=False):
                try:
                    envelope_dict = json.loads(message.body)
                    headers = dict(message.headers or {})
                    await handler(envelope_dict, headers)
                except Exception:
                    log.exception("handler failed; message will be dead-lettered")
                    raise

        await queue.consume(_on_message)
        import asyncio
        await asyncio.Future()
