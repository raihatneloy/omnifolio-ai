"""
Semantic Mapper — translates raw CSV/PDF headers into OmniFolio universal schema.

Uses the default LLM provider to semantically map source headers
to the OmniFolio schema via few-shot prompting. Falls back to the
LLMProvider base class's ``map_headers`` if the provider supports it,
but the primary path here is a standalone prompt crafted for high accuracy.
"""

from __future__ import annotations

import json
import re
from typing import Optional

from app.models import ColumnMapping
from app.services.llm.registry import get_registry


# ── Prompt builder ──────────────────────────────────────────────────────────


def _build_mapping_prompt(
    headers: list[str],
    sample_rows: list[list[str]],
) -> str:
    """Build a structured prompt with few-shot examples for the LLM.

    Parameters
    ----------
    headers:
        Column headers from the uploaded file.
    sample_rows:
        Up to 5 sample rows from the file to provide semantic context.

    Returns
    -------
    str
        The complete prompt string to send to the LLM.
    """
    headers_str = ", ".join(f'"{h}"' for h in headers)

    rows_lines = [" | ".join(cell for cell in row) for row in sample_rows]
    rows_str = "\n".join(rows_lines) if rows_lines else "(no sample rows)"

    prompt = f"""You are a financial data mapping assistant. Given the column headers of a portfolio CSV/PDF and sample rows, output ONLY valid JSON mapping each source column to the nearest OmniFolio schema field.

ALLOWED SCHEMA FIELDS:
- ticker: Stock/ETF ticker symbol (e.g., AAPL, VTI)
- quantity: Number of shares/units
- cost_basis: Total cost basis or cost per share
- txn_type: Transaction type (Buy, Sell, Dividend, etc.)
- txn_date: Transaction or acquisition date
- price: Price per share/unit
- fees: Trading fees or commissions
- asset_type: Type of asset (equity, bond, etf, etc.)
- account_id: Account identifier
- notes: Any column that doesn't fit elsewhere

RULES:
1. Map each source header to the schema field that best matches its meaning
2. Use null for any schema field not present in the source headers
3. If a column is ambiguous, map it to "notes" instead of guessing
4. Return ONLY valid JSON — no markdown, no explanation, no extra text
5. Match by semantic meaning, not by exact name

EXAMPLES:

Example 1 — Fidelity Holdings Report:
Source headers: ["Symbol", "Description", "Quantity", "Cost Basis", "Current Price", "Total Value"]
Sample rows:
AAPL | Apple Inc. | 100 | 15000.00 | 175.50 | 17550.00
Expected output:
{{"ticker": "Symbol", "quantity": "Quantity", "cost_basis": "Cost Basis", "price": "Current Price", "txn_type": null, "txn_date": null, "fees": null, "asset_type": null, "account_id": null, "notes": "Description"}}

Example 2 — Vanguard Transaction History:
Source headers: ["Ticker", "Transaction Type", "Shares", "Price", "Date", "Amount"]
Sample rows:
VTI | Buy | 50 | 245.00 | 2024-01-15 | 12250.00
Expected output:
{{"ticker": "Ticker", "txn_type": "Transaction Type", "quantity": "Shares", "price": "Price", "txn_date": "Date", "cost_basis": null, "fees": null, "asset_type": null, "account_id": null, "notes": null}}

Example 3 — Generic Broker (ambiguous headers):
Source headers: ["Asset", "Value", "Qty"]
Sample rows:
AAPL | 17550.00 | 100
Expected output:
{{"ticker": "Asset", "quantity": "Qty", "notes": "Value", "cost_basis": null, "txn_type": null, "txn_date": null, "price": null, "fees": null, "asset_type": null, "account_id": null}}

NOW MAP THESE HEADERS:

Source headers: [{headers_str}]

Sample rows:
{rows_str}

Respond ONLY with valid JSON (no markdown, no explanation)."""

    return prompt


# ── Response parser ─────────────────────────────────────────────────────────


def _parse_json_response(content: str) -> dict:
    """Extract and parse JSON from the LLM's response.

    Handles these response formats:

    * Pure JSON response (ideal)::

        {"ticker": "Symbol", ...}

    * JSON wrapped in markdown fenced block::

        ```json
        {"ticker": "Symbol", ...}
        ```

    * JSON with surrounding explanatory text.

    Parameters
    ----------
    content:
        The raw text returned by the LLM.

    Returns
    -------
    dict
        Parsed JSON dictionary.

    Raises
    ------
    ValueError
        If the response cannot be parsed as valid JSON.
    """
    # 1. Try to extract from a ```json ... ``` code block
    code_block = re.search(
        r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL
    )
    if code_block:
        json_str = code_block.group(1).strip()
    else:
        json_str = content.strip()

    # 2. If there's surrounding text, extract the JSON object
    brace = re.search(r"\{.*\}", json_str, re.DOTALL)
    if brace:
        json_str = brace.group(0)

    # 3. Attempt to parse
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse LLM response as JSON. "
            f"Response (first 500 chars): {content[:500]}"
        ) from exc


# ── Column mapping validation ───────────────────────────────────────────────


def _validate_mapping(
    parsed: dict,
    headers: list[str],
) -> dict:
    """Validate the parsed mapping against actual source headers.

    Ensures every non-null mapped value is a source header that actually
    exists (case-insensitive match). Unrecognised values are set to ``None``.

    Parameters
    ----------
    parsed:
        Raw dictionary returned by the LLM.
    headers:
        Original source column headers.

    Returns
    -------
    dict
        Cleaned mapping dictionary.
    """
    valid_headers_lower = {h.lower(): h for h in headers}

    cleaned: dict = {}
    for field in ColumnMapping.model_fields:
        val = parsed.get(field)
        if val is None:
            cleaned[field] = None
            continue

        if not isinstance(val, str) or not val.strip():
            cleaned[field] = None
            continue

        # Normalise the mapped value: find the actual header (case-insensitive)
        val_stripped = val.strip()
        matched = valid_headers_lower.get(val_stripped.lower())
        if matched:
            cleaned[field] = matched
        else:
            # The LLM may have returned a value not in headers — discard
            cleaned[field] = None

    return cleaned


# ── Public API ──────────────────────────────────────────────────────────────


async def map_headers(
    headers: list[str],
    sample_rows: list[list[str]],
) -> ColumnMapping:
    """Map raw file headers to OmniFolio universal schema fields.

    Uses the default LLM provider to semantically map source headers
    to the OmniFolio schema defined in :class:`ColumnMapping`.

    Parameters
    ----------
    headers:
        Column headers from the uploaded file, e.g.
        ``["Symbol", "Shares", "Cost Basis", "Date Acquired"]``.
    sample_rows:
        Up to 5 sample rows from the file to give the LLM context.

    Returns
    -------
    ColumnMapping
        A Pydantic model mapping target fields to source column names.

    Raises
    ------
    ValueError
        If the LLM response cannot be parsed as valid JSON.
    RuntimeError
        If no LLM provider is available.
    """
    provider = get_registry().get_default()

    prompt = _build_mapping_prompt(headers, sample_rows)

    response = await provider.complete(
        prompt=prompt,
        temperature=0.1,
        max_tokens=1024,
    )

    parsed = _parse_json_response(response.content)
    validated = _validate_mapping(parsed, headers)

    return ColumnMapping(**validated)
