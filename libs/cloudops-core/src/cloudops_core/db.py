from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def make_engine(dsn: str) -> AsyncEngine:
    """
    Cria um engine asyncpg. `dsn` deve estar no formato
    postgresql+asyncpg://user:pw@host:port/dbname
    """
    return create_async_engine(dsn, pool_pre_ping=True, pool_size=5, max_overflow=10)


def make_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
