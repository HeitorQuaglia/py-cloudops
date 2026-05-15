import os

from cloudops_core.db import make_engine, make_sessionmaker

DSN = os.getenv(
    "CATALOG_DB_DSN",
    "postgresql+asyncpg://catalog:catalog_pw@postgres:5432/catalog_db",
)

engine = make_engine(DSN)
SessionMaker = make_sessionmaker(engine)
