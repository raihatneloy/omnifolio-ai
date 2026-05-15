"""Tests for Pydantic v2 models and SQLAlchemy ORM models."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.models import (
    AssetType,
    ColumnMapping,
    HealthCheck,
    Holding,
    HoldingBase,
    IngestionError,
    IngestionResult,
    ReadinessCheck,
    Transaction,
    TransactionBase,
    TransactionType,
)


# ═══════════════════════════════════════════════════════════
#  Enums
# ═══════════════════════════════════════════════════════════


class TestAssetType:
    def test_values(self):
        assert AssetType.EQUITY.value == "equity"
        assert AssetType.BOND.value == "bond"
        assert AssetType.ETF.value == "etf"
        assert AssetType.CRYPTO.value == "crypto"
        assert AssetType.OPTION.value == "option"
        assert AssetType.MUTUAL_FUND.value == "mutual_fund"


class TestTransactionType:
    def test_values(self):
        assert TransactionType.BUY.value == "buy"
        assert TransactionType.SELL.value == "sell"
        assert TransactionType.DIVIDEND.value == "dividend"
        assert TransactionType.FEE.value == "fee"
        assert TransactionType.TRANSFER.value == "transfer"


# ═══════════════════════════════════════════════════════════
#  HoldingBase
# ═══════════════════════════════════════════════════════════


class TestHoldingBase:
    def test_valid_creation(self):
        h = HoldingBase(ticker="AAPL", quantity=10, cost_basis=1500.0)
        assert h.ticker == "AAPL"
        assert h.quantity == 10
        assert h.cost_basis == 1500.0
        assert h.asset_type == AssetType.EQUITY

    def test_ticker_normalised_to_upper(self):
        h = HoldingBase(ticker="aapl", quantity=1)
        assert h.ticker == "AAPL"

    def test_ticker_stripped(self):
        h = HoldingBase(ticker="  aapl  ", quantity=1)
        assert h.ticker == "AAPL"

    def test_empty_ticker_rejected(self):
        with pytest.raises(ValidationError):
            HoldingBase(ticker="   ", quantity=1)

    def test_negative_quantity_rejected(self):
        with pytest.raises(ValidationError):
            HoldingBase(ticker="AAPL", quantity=-1)

    def test_zero_quantity_rejected(self):
        with pytest.raises(ValidationError):
            HoldingBase(ticker="AAPL", quantity=0)

    def test_negative_cost_basis_rejected(self):
        with pytest.raises(ValidationError):
            HoldingBase(ticker="AAPL", quantity=1, cost_basis=-10)

    def test_optional_cost_basis(self):
        h = HoldingBase(ticker="AAPL", quantity=1)
        assert h.cost_basis is None


# ═══════════════════════════════════════════════════════════
#  Holding
# ═══════════════════════════════════════════════════════════


class TestHolding:
    def test_has_uuid_id(self):
        h = Holding(ticker="AAPL", quantity=10)
        assert isinstance(h.id, UUID)

    def test_has_timestamps(self):
        h = Holding(ticker="AAPL", quantity=10)
        assert isinstance(h.created_at, datetime)
        assert isinstance(h.updated_at, datetime)

    def test_serialization_roundtrip(self):
        h = Holding(ticker="AAPL", quantity=10, cost_basis=1500.0)
        data = h.model_dump()
        h2 = Holding(**data)
        assert h2.ticker == "AAPL"
        assert h2.quantity == 10
        assert h2.cost_basis == 1500.0


# ═══════════════════════════════════════════════════════════
#  TransactionBase
# ═══════════════════════════════════════════════════════════


class TestTransactionBase:
    def test_valid_creation(self):
        t = TransactionBase(ticker="AAPL", quantity=10, price=150.0)
        assert t.ticker == "AAPL"
        assert t.quantity == 10
        assert t.price == 150.0
        assert t.txn_type == TransactionType.BUY
        assert t.fees == 0.0

    def test_custom_txn_type(self):
        t = TransactionBase(
            ticker="AAPL", quantity=5, price=200.0, txn_type=TransactionType.SELL
        )
        assert t.txn_type == TransactionType.SELL

    def test_ticker_normalised(self):
        t = TransactionBase(ticker="aapl", quantity=1, price=100.0)
        assert t.ticker == "AAPL"

    def test_negative_price_rejected(self):
        with pytest.raises(ValidationError):
            TransactionBase(ticker="AAPL", quantity=1, price=-100.0)

    def test_zero_price_rejected(self):
        with pytest.raises(ValidationError):
            TransactionBase(ticker="AAPL", quantity=1, price=0)


# ═══════════════════════════════════════════════════════════
#  Transaction
# ═══════════════════════════════════════════════════════════


class TestTransaction:
    def test_has_uuid_id(self):
        t = Transaction(ticker="AAPL", quantity=10, price=150.0)
        assert isinstance(t.id, UUID)

    def test_has_timestamps(self):
        t = Transaction(ticker="AAPL", quantity=10, price=150.0)
        assert isinstance(t.created_at, datetime)

    def test_serialization_roundtrip(self):
        t = Transaction(
            ticker="AAPL",
            quantity=5,
            price=200.0,
            txn_type=TransactionType.SELL,
            fees=1.50,
        )
        data = t.model_dump()
        t2 = Transaction(**data)
        assert t2.ticker == "AAPL"
        assert t2.quantity == 5
        assert t2.price == 200.0
        assert t2.txn_type == TransactionType.SELL


# ═══════════════════════════════════════════════════════════
#  IngestionResult
# ═══════════════════════════════════════════════════════════


class TestIngestionResult:
    def test_needs_review_true_by_default(self):
        # Raw ingested data always needs human review before save (financial data safety)
        r = IngestionResult(source_file="test.csv", source_type="csv")
        assert r.needs_review is True

    def test_needs_review_true_when_errors(self):
        r = IngestionResult(
            source_file="test.csv",
            source_type="csv",
            errors=[IngestionError(row=1, message="bad data")],
        )
        assert r.needs_review is True

    def test_needs_review_still_true_with_clean_holdings(self):
        # Even with valid holdings and no errors, raw ingestion defaults to needs_review=True
        # (human review required before data is persisted)
        r = IngestionResult(
            source_file="test.csv",
            source_type="csv",
            holdings=[Holding(ticker="AAPL", quantity=10)],
            errors=[],
        )
        assert r.needs_review is True

    def test_column_mapping(self):
        r = IngestionResult(
            source_file="test.csv",
            source_type="csv",
            mapped_columns=ColumnMapping(ticker="Symbol", quantity="Shares"),
        )
        assert r.mapped_columns.ticker == "Symbol"
        assert r.mapped_columns.quantity == "Shares"

    def test_serialization(self):
        r = IngestionResult(
            source_file="test.csv",
            source_type="csv",
            holdings=[Holding(ticker="AAPL", quantity=5, cost_basis=500.0)],
            errors=[IngestionError(row=2, message="missing ticker")],
        )
        data = r.model_dump()
        assert data["source_file"] == "test.csv"
        assert len(data["holdings"]) == 1
        assert len(data["errors"]) == 1
        assert data["needs_review"] is True


# ═══════════════════════════════════════════════════════════
#  Health & Readiness
# ═══════════════════════════════════════════════════════════


class TestHealthCheck:
    def test_defaults(self):
        h = HealthCheck()
        assert h.status == "ok"


class TestReadinessCheck:
    def test_creation(self):
        r = ReadinessCheck(status="ready", postgres=True, redis=True)
        assert r.status == "ready"
        assert r.postgres is True
        assert r.redis is True


# ═══════════════════════════════════════════════════════════
#  SQLAlchemy ORM (import check only — no DB needed for unit)
# ═══════════════════════════════════════════════════════════


class TestDatabaseModels:
    def test_import_orm_models(self):
        from app.models.database_models import (
            Base,
            HoldingORM,
            IngestionLogORM,
            TransactionORM,
        )

        assert HoldingORM is not None
        assert TransactionORM is not None
        assert IngestionLogORM is not None
        assert Base is not None

    def test_orm_tables_have_expected_columns(self):
        from app.models.database_models import HoldingORM

        cols = HoldingORM.__table__.columns.keys()
        expected = {"id", "user_id", "ticker", "quantity", "cost_basis", "asset_type",
                     "created_at", "updated_at"}
        assert set(cols) == expected