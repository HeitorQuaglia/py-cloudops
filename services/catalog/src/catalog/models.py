from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Resource(Base):
    __tablename__ = "resources"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    type: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    owner: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False, default="PENDING")
    aws_arn: Mapped[str | None] = mapped_column(String, nullable=True)
    saga_id: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("type", "name", name="uq_resource_type_name"),)


class NameReservation(Base):
    __tablename__ = "name_reservations"
    name: Mapped[str] = mapped_column(String, primary_key=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    reserved_by_saga: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ProcessedMessage(Base):
    __tablename__ = "processed_messages"
    message_id: Mapped[str] = mapped_column(String, primary_key=True)
    handler: Mapped[str] = mapped_column(String, primary_key=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
