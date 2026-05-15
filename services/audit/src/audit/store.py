from typing import Any


class AuditStore:
    def __init__(self, db) -> None:
        self._events = db["events"]

    async def persist(self, envelope_dict: dict[str, Any]) -> None:
        doc = {
            "message_id": envelope_dict["message_id"],
            "saga_id": envelope_dict["correlation_id"],
            "type": envelope_dict["type"],
            "occurred_at": envelope_dict["occurred_at"],
            "causation_id": envelope_dict.get("causation_id"),
            "payload": envelope_dict.get("payload"),
        }
        await self._events.update_one(
            {"message_id": doc["message_id"], "type": doc["type"]},
            {"$setOnInsert": doc},
            upsert=True,
        )

    async def list_by_saga(self, saga_id: str) -> list[dict[str, Any]]:
        cursor = self._events.find({"saga_id": saga_id}).sort("occurred_at", 1)
        return [doc async for doc in cursor]
