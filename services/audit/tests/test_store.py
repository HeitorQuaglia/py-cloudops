import pytest
from mongomock_motor import AsyncMongoMockClient

from audit.store import AuditStore


@pytest.fixture
async def store():
    client = AsyncMongoMockClient()
    db = client["audit_db"]
    yield AuditStore(db)


async def test_persist_event_inserts_document(store):
    await store.persist(
        {
            "message_id": "m1",
            "correlation_id": "saga-1",
            "type": "evt.catalog.validate.completed",
            "occurred_at": "2026-05-15T00:00:00+00:00",
            "version": 1,
            "payload": {"ok": True},
        }
    )
    found = await store.list_by_saga("saga-1")
    assert len(found) == 1
    assert found[0]["type"] == "evt.catalog.validate.completed"
    assert found[0]["saga_id"] == "saga-1"
