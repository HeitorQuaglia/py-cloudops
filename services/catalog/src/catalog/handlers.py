from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from catalog.models import NameReservation, Resource


@dataclass
class HandlerReply:
    outcome: str  # "completed" | "failed"
    result: dict[str, Any] | None = None
    error: str | None = None


async def handle_validate(session: AsyncSession, *, payload: dict[str, Any]) -> HandlerReply:
    name = payload.get("name", "")
    if not name.islower() or not all(c.isalnum() or c == "-" for c in name):
        return HandlerReply(outcome="failed", error="name must be lowercase alphanumeric/hyphens")
    if len(name) < 3 or len(name) > 63:
        return HandlerReply(outcome="failed", error="name length must be 3..63")
    return HandlerReply(outcome="completed", result={"validated_name": name})


async def handle_reserve_name(
    session: AsyncSession, *, payload: dict[str, Any], saga_id: str
) -> HandlerReply:
    reservation = NameReservation(
        name=payload["name"],
        type=payload["type"],
        reserved_by_saga=saga_id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    session.add(reservation)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        return HandlerReply(outcome="failed", error="name already reserved")
    return HandlerReply(outcome="completed", result={"reserved": payload["name"]})


async def handle_register(
    session: AsyncSession, *, payload: dict[str, Any], saga_id: str
) -> HandlerReply:
    resource = Resource(
        type=payload["type"],
        name=payload["name"],
        owner=payload["owner"],
        state="ACTIVE",
        aws_arn=payload.get("aws_arn"),
        saga_id=saga_id,
    )
    session.add(resource)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        return HandlerReply(outcome="failed", error="resource already exists")
    return HandlerReply(outcome="completed", result={"resource_id": resource.id})


# Stubs para Iteração 2 — compensações
async def handle_release_name(
    session: AsyncSession, *, payload: dict[str, Any], saga_id: str
) -> HandlerReply:
    return HandlerReply(outcome="completed")  # implementação real na Iteração 2


async def handle_deregister(
    session: AsyncSession, *, payload: dict[str, Any], saga_id: str
) -> HandlerReply:
    return HandlerReply(outcome="completed")  # implementação real na Iteração 2
