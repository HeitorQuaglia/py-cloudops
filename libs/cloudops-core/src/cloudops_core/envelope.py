from datetime import datetime, timezone
from typing import Generic, TypeVar
from uuid import uuid4

from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class Envelope(BaseModel, Generic[T]):
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    correlation_id: str
    causation_id: str | None = None
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    type: str
    version: int = 1
    payload: T


def new_envelope(
    *,
    type_: str,
    payload: T,
    correlation_id: str,
    causation_id: str | None = None,
) -> Envelope[T]:
    return Envelope(
        type=type_,
        payload=payload,
        correlation_id=correlation_id,
        causation_id=causation_id,
    )
