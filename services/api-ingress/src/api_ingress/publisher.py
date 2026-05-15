import os

from cloudops_core.amqp import AmqpClient

_amqp: AmqpClient | None = None


async def get_publisher() -> AmqpClient:
    global _amqp
    if _amqp is None:
        _amqp = AmqpClient(url=os.getenv("AMQP_URL", "amqp://cloudops:cloudops_pw@rabbitmq:5672/"))
        await _amqp.connect()
    return _amqp
