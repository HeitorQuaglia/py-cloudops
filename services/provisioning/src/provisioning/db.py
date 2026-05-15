import os
from cloudops_core.db import make_engine, make_sessionmaker

DSN = os.getenv(
    "PROVISIONING_DB_DSN",
    "postgresql+asyncpg://provisioning:provisioning_pw@postgres:5432/provisioning_db",
)
engine = make_engine(DSN)
SessionMaker = make_sessionmaker(engine)
