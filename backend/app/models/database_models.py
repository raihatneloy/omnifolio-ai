"""SQLAlchemy ORM models for Omnifolio AI."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class HoldingORM(Base):
    __tablename__ = "holdings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    cost_basis = Column(Float, nullable=True)
    asset_type = Column(String(20), nullable=False, server_default="equity")
    created_at = Column(DateTime, nullable=False, server_default=text("NOW()"))
    updated_at = Column(
        DateTime, nullable=False, server_default=text("NOW()"), onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_holdings_user_ticker", "user_id", "ticker", unique=True),
    )


class TransactionORM(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    txn_type = Column(String(20), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    txn_date = Column(DateTime, nullable=False, index=True)
    fees = Column(Float, nullable=False, server_default="0")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("NOW()"))

    __table_args__ = (
        Index("ix_txns_user_date", "user_id", "txn_date"),
        Index("ix_txns_user_ticker_date", "user_id", "ticker", "txn_date"),
    )


class IngestionLogORM(Base):
    __tablename__ = "ingestion_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    source_file = Column(String(255), nullable=False)
    source_type = Column(String(10), nullable=False)  # csv | pdf
    status = Column(String(20), nullable=False, index=True)  # pending | completed | failed
    rows_parsed = Column(Float, nullable=True)
    rows_with_errors = Column(Float, nullable=True)
    needs_review = Column(Boolean, nullable=False, server_default="true")
    error_log = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("NOW()"))

    __table_args__ = (
        Index("ix_ingest_user_status", "user_id", "status"),
    )