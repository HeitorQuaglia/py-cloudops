from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


IDEMPOTENCY_DDL = """
CREATE TABLE IF NOT EXISTS processed_messages (
    message_id TEXT NOT NULL,
    handler TEXT NOT NULL,
    processed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (message_id, handler)
)
"""


async def claim_message(session: AsyncSession, *, message_id: str, handler: str) -> bool:
    """
    Insere (message_id, handler) em processed_messages.
    Retorna True se foi a primeira vez (caller deve processar) ou False se já processado.

    O caller é responsável pelo commit/rollback — esta função apenas faz o INSERT.
    """
    try:
        await session.execute(
            text(
                "INSERT INTO processed_messages (message_id, handler, processed_at) "
                "VALUES (:mid, :h, now())"
            ),
            {"mid": message_id, "h": handler},
        )
        await session.flush()
        return True
    except IntegrityError:
        await session.rollback()
        return False
