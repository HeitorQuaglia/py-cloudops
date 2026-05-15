from datetime import datetime
from uuid import uuid4
from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Saga(Base):
    __tablename__ = "sagas"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    type: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False, default="PENDING")
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    version: Mapped[int] = mapped_column(Integer, default=1)


class SagaStep(Base):
    __tablename__ = "saga_steps"
    saga_id: Mapped[str] = mapped_column(String, primary_key=True)
    step_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDING")
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(String)


class ProcessedMessage(Base):
    __tablename__ = "processed_messages"
    message_id: Mapped[str] = mapped_column(String, primary_key=True)
    handler: Mapped[str] = mapped_column(String, primary_key=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Outbox(Base):
    __tablename__ = "outbox"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    saga_id: Mapped[str | None] = mapped_column(String)
    exchange: Mapped[str] = mapped_column(String, nullable=False)
    routing_key: Mapped[str] = mapped_column(String, nullable=False)
    envelope: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
