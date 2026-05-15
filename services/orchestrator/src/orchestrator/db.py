import os
from cloudops_core.db import make_engine, make_sessionmaker

DSN = os.getenv(
    "ORCHESTRATOR_DB_DSN",
    "postgresql+asyncpg://orchestrator:orchestrator_pw@postgres:5432/orchestrator_db",
)
engine = make_engine(DSN)
SessionMaker = make_sessionmaker(engine)
