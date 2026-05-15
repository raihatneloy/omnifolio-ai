"""Models package — Pydantic v2 models for the application."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Enums ─────────────────────────────────────────────────


class AssetType(str, Enum):
    EQUITY = "equity"
    BOND = "bond"
    ETF = "etf"
    CRYPTO = "crypto"
    OPTION = "option"
    MUTUAL_FUND = "mutual_fund"


class TransactionType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    FEE = "fee"
    TRANSFER = "transfer"


# ── Error Model ───────────────────────────────────────────


class IngestionError(BaseModel):
    """A single error encountered during ingestion."""

    row: Optional[int] = None
    column: Optional[str] = None
    message: str


# ── Column Mapping ────────────────────────────────────────


class ColumnMapping(BaseModel):
    """Maps raw CSV/PDF headers to universal schema fields."""

    ticker: Optional[str] = None
    quantity: Optional[str] = None
    cost_basis: Optional[str] = None
    txn_type: Optional[str] = None
    txn_date: Optional[str] = None
    price: Optional[str] = None
    fees: Optional[str] = None
    asset_type: Optional[str] = None
    account_id: Optional[str] = None
    notes: Optional[str] = None


# ── Base Models ───────────────────────────────────────────


class HoldingBase(BaseModel):
    """Base holding fields shared across create/update."""

    ticker: str = Field(..., description="Uppercase ticker symbol, e.g. AAPL")
    quantity: float = Field(gt=0, description="Number of shares/units, must be > 0")
    cost_basis: Optional[float] = Field(
        None, ge=0, description="Total cost basis in USD, must be >= 0"
    )
    asset_type: AssetType = AssetType.EQUITY

    @field_validator("ticker")
    @classmethod
    def normalise_ticker(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("ticker must not be empty")
        return v


class TransactionBase(BaseModel):
    """Base transaction fields shared across create/update."""

    ticker: str = Field(..., description="Uppercase ticker symbol")
    txn_type: TransactionType = TransactionType.BUY
    quantity: float = Field(gt=0, description="Number of shares, must be > 0")
    price: float = Field(gt=0, description="Price per share in USD, must be > 0")
    txn_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    fees: float = Field(default=0.0, ge=0, description="Fees in USD, must be >= 0")

    @field_validator("ticker")
    @classmethod
    def normalise_ticker(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("ticker must not be empty")
        return v


# ── Full Models (with id & timestamps) ────────────────────


class Holding(HoldingBase):
    """Full holding with metadata."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Transaction(TransactionBase):
    """Full transaction with metadata."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Ingestion Result ──────────────────────────────────────


class IngestionResult(BaseModel):
    """Result of an ingestion run (CSV or PDF)."""

    source_file: str = Field(..., description="Original filename")
    source_type: str = Field(..., description="csv or pdf")
    mapped_columns: Optional[ColumnMapping] = None
    holdings: list[Holding] = Field(default_factory=list)
    transactions: list[Transaction] = Field(default_factory=list)
    errors: list[IngestionError] = Field(default_factory=list)
    needs_review: bool = True

    @model_validator(mode="after")
    def auto_set_needs_review(self) -> IngestionResult:
        """Set needs_review=True whenever there are errors."""
        if self.errors:
            self.needs_review = True
        return self


# ── Health & Readiness ────────────────────────────────────


class HealthCheck(BaseModel):
    """Response model for GET /health."""

    status: str = "ok"


class ReadinessCheck(BaseModel):
    """Response model for GET /ready."""

    status: str
    postgres: bool
    redis: bool