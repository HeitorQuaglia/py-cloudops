import asyncio
import os

from motor.motor_asyncio import AsyncIOMotorClient

from audit.store import AuditStore
from cloudops_core.amqp import AmqpClient
from cloudops_core.logging import configure_logging, get_logger

AMQP_URL = os.getenv("AMQP_URL", "amqp://cloudops:cloudops_pw@rabbitmq:5672/")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://audit:audit_pw@mongodb:27017/?authSource=admin")
MONGO_DB = os.getenv("MONGO_DB", "audit_db")

log = get_logger()


async def main() -> None:
    configure_logging(service="audit")
    client = AsyncIOMotorClient(MONGO_URL)
    store = AuditStore(client[MONGO_DB])
    await store._events.create_index([("saga_id", 1), ("occurred_at", 1)])
    await store._events.create_index([("type", 1), ("occurred_at", -1)])

    amqp = AmqpClient(url=AMQP_URL)
    await amqp.connect()

    async def handler(envelope_dict, headers):
        try:
            await store.persist(envelope_dict)
            log.info("persisted", type=envelope_dict.get("type"), saga_id=envelope_dict.get("correlation_id"))
        except Exception:
            log.exception("persist_failed")

    log.info("starting", queue="audit.all")
    await amqp.consume("audit.all", handler)


if __name__ == "__main__":
    asyncio.run(main())
