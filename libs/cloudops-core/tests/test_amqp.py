import asyncio
import os

import pytest
from pydantic import BaseModel

from cloudops_core.amqp import AmqpClient
from cloudops_core.envelope import new_envelope

pytestmark = pytest.mark.integration

AMQP_URL = os.getenv("TEST_AMQP_URL", "amqp://cloudops:cloudops_pw@localhost:5672/")


class Hello(BaseModel):
    greeting: str


async def test_publish_and_consume_roundtrip():
    received: list[dict] = []

    client = AmqpClient(url=AMQP_URL)
    await client.connect()

    routing_key = "evt.test.hello"
    queue_name = "test.hello.queue"
    await client.declare_queue(queue_name, exchange="cloudops.events", routing_key=routing_key)

    async def handler(envelope_dict, headers):
        received.append(envelope_dict)

    consume_task = asyncio.create_task(client.consume(queue_name, handler))

    env = new_envelope(type_=routing_key, payload=Hello(greeting="hi"), correlation_id="c-1")
    await client.publish(exchange="cloudops.events", routing_key=routing_key, envelope=env)

    for _ in range(50):
        if received:
            break
        await asyncio.sleep(0.1)

    consume_task.cancel()
    await client.close()

    assert len(received) == 1
    assert received[0]["correlation_id"] == "c-1"
    assert received[0]["payload"]["greeting"] == "hi"
