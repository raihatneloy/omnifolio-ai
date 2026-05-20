"""
Tests for the Semantic Mapper (Chunk 1.2).

Tests the ``map_headers`` function in ``app.services.mapper`` by mocking
the LLM provider to return controlled responses.  Covers:
* Exact match headers
* Synonym-based headers
* Missing / partial fields
* Ambiguous headers
* Invalid JSON / markdown-wrapped responses
* Golden Test Cases from the design doc
"""

from __future__ import annotations

import json
import re
from typing import Optional

import pytest

from app.models import ColumnMapping
from app.services.llm.base import LLMProvider, LLMResponse
from app.services.llm.registry import ProviderRegistry, get_registry
from app.services.mapper import (
    _build_mapping_prompt,
    _parse_json_response,
    _validate_mapping,
    map_headers,
)


# ── Mock provider ───────────────────────────────────────────────────────────


class MockLLMProvider(LLMProvider):
    """A stub LLM provider that returns a preset JSON response."""

    name: str = "mock"
    default_model: str = "mock/test"

    def __init__(self, response_json: Optional[dict] = None) -> None:
        self._response_json = response_json or {}

    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        content = json.dumps(self._response_json)
        return LLMResponse(content=content, model=self.default_model)


class MockLLMProviderRaw(LLMProvider):
    """A stub provider that returns a raw string (not necessarily valid JSON)."""

    name: str = "mock-raw"
    default_model: str = "mock/test"

    def __init__(self, raw_content: str = "") -> None:
        self._raw_content = raw_content

    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        return LLMResponse(content=self._raw_content, model=self.default_model)


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clean_registry() -> None:
    """Ensure a fresh registry for each test — no cross-test leakage."""
    reg = ProviderRegistry()
    import app.services.llm.registry as reg_mod

    # monkeypatch the global singleton
    reg_mod.registry = reg
    # also patch get_registry to return our fresh one
    original = reg_mod.get_registry

    def _fresh_registry() -> ProviderRegistry:
        return reg

    reg_mod.get_registry = _fresh_registry
    yield
    reg_mod.get_registry = original


# ── Prompt builder ──────────────────────────────────────────────────────────


class TestBuildMappingPrompt:
    def test_headers_included(self) -> None:
        prompt = _build_mapping_prompt(["Symbol", "Shares"], [["AAPL", "100"]])
        assert "Symbol" in prompt
        assert "Shares" in prompt

    def test_sample_rows_included(self) -> None:
        prompt = _build_mapping_prompt(
            ["Ticker", "Qty"], [["AAPL", "100"], ["MSFT", "50"]]
        )
        assert "AAPL" in prompt
        assert "MSFT" in prompt
        assert "100" in prompt
        assert "50" in prompt

    def test_examples_present(self) -> None:
        prompt = _build_mapping_prompt(["X"], [["Y"]])
        assert "Example 1" in prompt or "Fidelity" in prompt
        assert "Vanguard" in prompt
        assert "SCHEMA" in prompt

    def test_target_fields_listed(self) -> None:
        prompt = _build_mapping_prompt(["A"], [["B"]])
        for field in ColumnMapping.model_fields:
            assert field in prompt

    def test_no_rows_handled(self) -> None:
        prompt = _build_mapping_prompt(["A"], [])
        assert "no sample rows" in prompt or "(no sample rows)" in prompt


# ── JSON response parser ────────────────────────────────────────────────────


class TestParseJsonResponse:
    def test_pure_json(self) -> None:
        result = _parse_json_response('{"ticker": "Symbol"}')
        assert result == {"ticker": "Symbol"}

    def test_markdown_code_block(self) -> None:
        result = _parse_json_response(
            '```json\n{"ticker": "Symbol", "quantity": "Qty"}\n```'
        )
        assert result == {"ticker": "Symbol", "quantity": "Qty"}

    def test_markdown_no_lang(self) -> None:
        result = _parse_json_response(
            '```\n{"ticker": "Symbol"}\n```'
        )
        assert result == {"ticker": "Symbol"}

    def test_surrounding_text(self) -> None:
        result = _parse_json_response(
            'Here is the mapping:\n{"ticker": "Symbol"}\nHope this helps.'
        )
        assert result == {"ticker": "Symbol"}

    def test_empty_object(self) -> None:
        result = _parse_json_response("{}")
        assert result == {}

    def test_invalid_json_raises(self) -> None:
        with pytest.raises(ValueError, match="Failed to parse"):
            _parse_json_response("not json at all")

    def test_partial_json_raises(self) -> None:
        with pytest.raises(ValueError, match="Failed to parse"):
            _parse_json_response('{"ticker": "Symbol"')


# ── Mapping validation ─────────────────────────────────────────────────────


class TestValidateMapping:
    def test_exact_match(self) -> None:
        parsed = {"ticker": "Symbol", "quantity": "Quantity"}
        result = _validate_mapping(parsed, ["Symbol", "Quantity"])
        assert result["ticker"] == "Symbol"
        assert result["quantity"] == "Quantity"
        assert result["cost_basis"] is None

    def test_case_insensitive_match(self) -> None:
        parsed = {"ticker": "symbol", "quantity": "QUANTITY"}
        result = _validate_mapping(parsed, ["Symbol", "Quantity"])
        assert result["ticker"] == "Symbol"
        assert result["quantity"] == "Quantity"

    def test_value_not_in_headers_is_nulled(self) -> None:
        parsed = {"ticker": "Ticker"}
        result = _validate_mapping(parsed, ["Symbol"])
        assert result["ticker"] is None

    def test_null_values_preserved(self) -> None:
        parsed = {"ticker": "Symbol", "quantity": None}
        result = _validate_mapping(parsed, ["Symbol"])
        assert result["ticker"] == "Symbol"
        assert result["quantity"] is None

    def test_empty_string_is_nulled(self) -> None:
        parsed = {"ticker": ""}
        result = _validate_mapping(parsed, ["Symbol"])
        assert result["ticker"] is None

    def test_all_fields_present(self) -> None:
        parsed = {
            "ticker": "Ticker",
            "quantity": "Qty",
            "cost_basis": "Cost",
            "txn_type": "Action",
            "txn_date": "Date",
            "price": "Price",
            "fees": "Commission",
            "asset_type": "Type",
            "account_id": "Account",
            "notes": "Notes",
        }
        headers = [
            "Ticker", "Qty", "Cost", "Action", "Date",
            "Price", "Commission", "Type", "Account", "Notes",
        ]
        result = _validate_mapping(parsed, headers)
        assert result["ticker"] == "Ticker"
        assert result["quantity"] == "Qty"
        assert result["cost_basis"] == "Cost"
        assert result["txn_type"] == "Action"
        assert result["fees"] == "Commission"
        assert result["notes"] == "Notes"

    def test_extra_fields_in_parsed_ignored(self) -> None:
        parsed = {"ticker": "Symbol", "extra_field": "Value"}
        result = _validate_mapping(parsed, ["Symbol"])
        assert result["ticker"] == "Symbol"
        assert "extra_field" not in result


# ── map_headers integration ─────────────────────────────────────────────────


class TestMapHeaders:
    """Tests that exercise the full ``map_headers`` pipeline with a mock provider."""

    @pytest.mark.asyncio
    async def test_exact_match_headers(self) -> None:
        """Golden Test Case: Exact match — each header maps directly."""
        provider = MockLLMProvider(
            {
                "ticker": "Symbol",
                "quantity": "Quantity",
                "cost_basis": "Cost Basis",
                "txn_type": None,
                "txn_date": None,
                "price": "Price",
                "fees": None,
                "asset_type": None,
                "account_id": None,
                "notes": None,
            }
        )
        reg = get_registry()
        reg.register("mock", provider)

        result = await map_headers(
            headers=["Symbol", "Quantity", "Cost Basis", "Price"],
            sample_rows=[["AAPL", "100", "15000.00", "150.00"]],
        )
        assert isinstance(result, ColumnMapping)
        assert result.ticker == "Symbol"
        assert result.quantity == "Quantity"
        assert result.cost_basis == "Cost Basis"
        assert result.price == "Price"
        assert result.txn_type is None
        assert result.fees is None

    @pytest.mark.asyncio
    async def test_synonym_headers(self) -> None:
        """Golden Test Case: Synonyms — headers use different names."""
        provider = MockLLMProvider(
            {
                "ticker": "Ticker",
                "quantity": "Shares",
                "cost_basis": "Cost Basis",
                "txn_type": "Action",
                "txn_date": "Date",
                "price": "Price",
                "fees": None,
                "asset_type": None,
                "account_id": None,
                "notes": None,
            }
        )
        reg = get_registry()
        reg.register("mock", provider)

        result = await map_headers(
            headers=["Ticker", "Shares", "Cost Basis", "Action", "Date", "Price"],
            sample_rows=[["VTI", "50", "12250.00", "Buy", "2024-01-15", "245.00"]],
        )
        assert isinstance(result, ColumnMapping)
        assert result.ticker == "Ticker"
        assert result.quantity == "Shares"
        assert result.txn_type == "Action"
        assert result.txn_date == "Date"
        assert result.price == "Price"

    @pytest.mark.asyncio
    async def test_missing_fields_all_null(self) -> None:
        """Golden Test Case: Minimal headers — most fields should be null."""
        provider = MockLLMProvider(
            {
                "ticker": "Symbol",
                "quantity": "Qty",
                "cost_basis": None,
                "txn_type": None,
                "txn_date": None,
                "price": None,
                "fees": None,
                "asset_type": None,
                "account_id": None,
                "notes": None,
            }
        )
        reg = get_registry()
        reg.register("mock", provider)

        result = await map_headers(
            headers=["Symbol", "Qty"],
            sample_rows=[["AAPL", "100"]],
        )
        assert result.ticker == "Symbol"
        assert result.quantity == "Qty"
        assert result.cost_basis is None
        assert result.txn_type is None
        assert result.txn_date is None
        assert result.price is None
        assert result.fees is None
        assert result.asset_type is None
        assert result.account_id is None
        assert result.notes is None

    @pytest.mark.asyncio
    async def test_ambiguous_headers_mapped_to_notes(self) -> None:
        """Golden Test Case: Ambiguous column mapped to notes."""
        provider = MockLLMProvider(
            {
                "ticker": "Symbol",
                "quantity": "Qty",
                "cost_basis": None,
                "txn_type": None,
                "txn_date": None,
                "price": None,
                "fees": None,
                "asset_type": None,
                "account_id": None,
                "notes": "Description",
            }
        )
        reg = get_registry()
        reg.register("mock", provider)

        result = await map_headers(
            headers=["Symbol", "Qty", "Description"],
            sample_rows=[["AAPL", "100", "Apple Inc."]],
        )
        assert isinstance(result, ColumnMapping)
        assert result.ticker == "Symbol"
        assert result.quantity == "Qty"
        assert result.notes == "Description"

    @pytest.mark.asyncio
    async def test_fidelity_holdings_golden(self) -> None:
        """Golden Test Case: Fidelity Holdings Report."""
        provider = MockLLMProvider(
            {
                "ticker": "Symbol",
                "quantity": "Quantity",
                "cost_basis": "Cost Basis",
                "txn_type": None,
                "txn_date": None,
                "price": "Current Price",
                "fees": None,
                "asset_type": None,
                "account_id": None,
                "notes": "Description",
            }
        )
        reg = get_registry()
        reg.register("mock", provider)

        result = await map_headers(
            headers=["Symbol", "Description", "Quantity", "Cost Basis", "Current Price", "Total Value"],
            sample_rows=[["AAPL", "Apple Inc.", "100", "15000.00", "175.50", "17550.00"]],
        )
        assert result.ticker == "Symbol"
        assert result.quantity == "Quantity"
        assert result.cost_basis == "Cost Basis"
        assert result.price == "Current Price"
        assert result.notes == "Description"
        assert result.txn_date is None
        assert result.fees is None

    @pytest.mark.asyncio
    async def test_vanguard_transactions_golden(self) -> None:
        """Golden Test Case: Vanguard Transaction History."""
        provider = MockLLMProvider(
            {
                "ticker": "Ticker",
                "quantity": "Shares",
                "cost_basis": None,
                "txn_type": "Transaction Type",
                "txn_date": "Date",
                "price": "Price",
                "fees": None,
                "asset_type": None,
                "account_id": None,
                "notes": None,
            }
        )
        reg = get_registry()
        reg.register("mock", provider)

        result = await map_headers(
            headers=["Ticker", "Transaction Type", "Shares", "Price", "Date", "Amount"],
            sample_rows=[["VTI", "Buy", "50", "245.00", "2024-01-15", "12250.00"]],
        )
        assert result.ticker == "Ticker"
        assert result.quantity == "Shares"
        assert result.txn_type == "Transaction Type"
        assert result.txn_date == "Date"
        assert result.price == "Price"
        assert result.cost_basis is None
        assert result.fees is None

    @pytest.mark.asyncio
    async def test_response_from_markdown_block(self) -> None:
        """LLM response wrapped in ```json ... ``` should still parse."""
        provider = MockLLMProviderRaw(
            raw_content='''Here is the mapping you requested:
```json
{"ticker": "Symbol", "quantity": "Quantity"}
```
I hope this helps!'''
        )
        reg = get_registry()
        reg.register("mockraw", provider)

        result = await map_headers(
            headers=["Symbol", "Quantity"],
            sample_rows=[["AAPL", "100"]],
        )
        assert result.ticker == "Symbol"
        assert result.quantity == "Quantity"

    @pytest.mark.asyncio
    async def test_invalid_json_response_raises(self) -> None:
        """Invalid JSON from LLM should raise ValueError."""
        provider = MockLLMProviderRaw(raw_content="This is not JSON at all")
        reg = get_registry()
        reg.register("mockbad", provider)

        with pytest.raises(ValueError, match="Failed to parse"):
            await map_headers(
                headers=["Symbol"],
                sample_rows=[["AAPL"]],
            )

    @pytest.mark.asyncio
    async def test_no_registered_provider_raises(self) -> None:
        """Calling map_headers with no registered provider raises RuntimeError."""
        # Registry is empty (fixture cleaned it)
        with pytest.raises(Exception, match="No enabled"):
            await map_headers(
                headers=["Symbol"],
                sample_rows=[["AAPL"]],
            )

    @pytest.mark.asyncio
    async def test_partial_mapping(self) -> None:
        """Only a subset of fields is mapped; the rest should be None."""
        provider = MockLLMProvider(
            {
                "ticker": "Ticker",
                "quantity": "Qty",
                "cost_basis": None,
                "txn_type": None,
                "txn_date": None,
                "price": None,
                "fees": None,
                "asset_type": None,
                "account_id": None,
                "notes": None,
            }
        )
        reg = get_registry()
        reg.register("mock", provider)

        result = await map_headers(
            headers=["Ticker", "Qty"],
            sample_rows=[["AAPL", "100"]],
        )
        assert result.ticker == "Ticker"
        assert result.quantity == "Qty"
        assert result.price is None
        assert result.txn_date is None

    @pytest.mark.asyncio
    async def test_case_insensitive_header_matching(self) -> None:
        """LLM may return lowercase header name; validation should normalise."""
        provider = MockLLMProvider(
            {
                "ticker": "symbol",
                "quantity": "qty",
            }
        )
        reg = get_registry()
        reg.register("mock", provider)

        result = await map_headers(
            headers=["Symbol", "Qty"],
            sample_rows=[["AAPL", "100"]],
        )
        assert result.ticker == "Symbol"  # should match the actual header casing
        assert result.quantity == "Qty"

    @pytest.mark.asyncio
    async def test_empty_headers_list(self) -> None:
        """Empty headers list should produce a mapping with all nulls."""
        provider = MockLLMProvider({})
        reg = get_registry()
        reg.register("mock", provider)

        result = await map_headers(
            headers=[],
            sample_rows=[],
        )
        assert isinstance(result, ColumnMapping)
        for field in ColumnMapping.model_fields:
            assert getattr(result, field) is None
