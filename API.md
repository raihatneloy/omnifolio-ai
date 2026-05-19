# Omnifolio AI — API Reference

> **Note:** Full interactive documentation is available at:
> - Swagger UI: `http://localhost:8000/docs`
> - ReDoc: `http://localhost:8000/redoc`
> - OpenAPI JSON: `http://localhost:8000/openapi.json`

> This document supplements the auto-generated docs with human-readable descriptions and usage examples.

---

## Table of Contents

1. [Health & Readiness](#1-health--readiness)
2. [Holdings](#2-holdings)
3. [Transactions](#3-transactions)
4. [Upload](#4-upload)
5. [Review](#5-review)
6. [LLM Provider Registry](#6-llm-provider-registry)

---

## 1. Health & Readiness

### `GET /health`

**Liveness probe** — confirms the app process is alive. No DB or Redis required.

**Response**
```json
{ "status": "ok" }
```

**Used by:** Load balancers, container healthchecks.

---

### `GET /health/ready`

**Readiness probe** — confirms the app is ready to serve traffic (DB connected, Redis reachable, etc.).

> ⚠️ Currently a stub. Will be wired to actual dependency checks in Phase 2.

**Response**
```json
{ "status": "ready" }
```

---

## 2. Holdings

Investment positions (stocks, bonds, ETFs, crypto, options, mutual funds).

### `GET /holdings`

List all holdings.

**Response** `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "ticker": "AAPL",
    "quantity": 10.0,
    "cost_basis": 1500.00,
    "asset_type": "equity",
    "created_at": "2026-05-15T09:00:00Z",
    "updated_at": "2026-05-15T09:00:00Z"
  }
]
```

---

### `GET /holdings/{holding_id}`

Get a single holding by ID.

**Response** `200 OK` — the holding object above.

**Errors:**
- `404 Not Found` — holding does not exist.

---

### `POST /holdings`

Create a new holding.

**Request body**
```json
{
  "ticker": "AAPL",
  "quantity": 10.0,
  "cost_basis": 1500.00,
  "asset_type": "equity"
}
```

**Constraints:**
- `ticker`: required, non-empty string, normalized to uppercase and stripped of whitespace.
- `quantity`: required, must be `> 0`.
- `cost_basis`: optional, must be `>= 0` if provided.
- `asset_type`: required, one of `equity | bond | etf | crypto | option | mutual_fund`.

**Response** `201 Created` — returns the full `Holding` object with `id` and timestamps.

---

### `DELETE /holdings/{holding_id}`

Delete a holding by ID.

**Response** `204 No Content`

**Errors:**
- `404 Not Found` — holding does not exist.

---

## 3. Transactions

Buy/sell/dividend/fee/transfer events associated with holdings.

### `GET /transactions`

List all transactions.

**Response** `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "ticker": "AAPL",
    "transaction_type": "buy",
    "quantity": 5.0,
    "price": 150.00,
    "currency": "USD",
    "transaction_date": "2026-01-15",
    "notes": null,
    "created_at": "2026-05-15T09:00:00Z",
    "updated_at": "2026-05-15T09:00:00Z"
  }
]
```

---

### `GET /transactions/{tx_id}`

Get a single transaction by ID.

**Response** `200 OK` — the transaction object above.

**Errors:**
- `404 Not Found` — transaction does not exist.

---

### `POST /transactions`

Create a new transaction.

**Request body**
```json
{
  "ticker": "AAPL",
  "transaction_type": "buy",
  "quantity": 5.0,
  "price": 150.00,
  "currency": "USD",
  "transaction_date": "2026-01-15",
  "notes": "Bought on dip"
}
```

**Constraints:**
- `ticker`: required, normalized to uppercase.
- `transaction_type`: required, one of `buy | sell | dividend | fee | transfer`.
- `quantity`: required, must be `> 0`.
- `price`: required, must be `>= 0`.
- `currency`: optional, defaults to `USD`.
- `transaction_date`: optional, ISO 8601 date string.

**Response** `201 Created` — returns the full `Transaction` object with `id` and timestamps.

---

### `DELETE /transactions/{tx_id}`

Delete a transaction by ID.

**Response** `204 No Content`

**Errors:**
- `404 Not Found` — transaction does not exist.

---

## 4. Upload

CSV/PDF file ingestion for AI-powered column mapping and holding extraction.

### `POST /upload`

Upload a CSV or PDF file for ingestion.

> ⚠️ Currently a stub — returns a placeholder `IngestionResult`. Real pipeline wired in **Phase 1** (Chunks 1.3–1.5).

**Request:** `multipart/form-data` with a `file` field.

**Accepted MIME types:** `text/csv`, `application/pdf`.

**Response** `201 Created`
```json
{
  "success": false,
  "message": "Upload stub — pipeline not yet wired. See Chunk 1.5.",
  "mappings": [],
  "holdings": [],
  "errors": [],
  "needs_review": true
}
```

**Errors:**
- `415 Unsupported Media Type` — file type is not CSV or PDF.

---

### `GET /upload/status/{job_id}`

Poll the status of an ingestion job.

> ⚠️ Currently a stub. Real job queue wired in **Phase 1** (Chunk 1.5) using Redis/Celery.

**Response** `200 OK` — placeholder `IngestionResult`.
```json
{
  "status": "pending"
}
```

---

## 5. Review

Approve or reject AI-generated ingestion results before they are persisted.

### `GET /review`

List all ingestion results awaiting human review.

> ⚠️ Currently returns an empty array. Real DB query wired in ** Phase 1** (Chunk 1.6), filtering by `needs_review=True`.

**Response** `200 OK`
```json
[]
```

---

### `POST /review/confirm/{result_id}`

Confirm a reviewed ingestion result — write holdings to the database.

> ⚠️ Currently a stub. Real DB write wired in **Phase 1** (Chunk 1.6).

**Response** `204 No Content`

---

### `POST /review/reject/{result_id}`

Reject and discard an ingestion result.

> ⚠️ Currently a stub. Real cleanup wired in **Phase 1** (Chunk 1.6).

**Response** `204 No Content`

---

## 6. LLM Provider Registry

Internal service for managing multiple LLM providers. This section describes the data models used by the ingestion pipeline.

### `LLMResponse` (Data Model)

Standardized response object for all LLM providers.

**Properties:**
- `content`: (string) The actual text response from the model.
- `model`: (string) The identifier of the model that generated the response.
- `tokens_used`: (integer | null) Total tokens consumed by the request.
- `raw`: (object | null) The raw JSON response from the provider for debugging.

### `LLMError` (Error Model)

Exception hierarchy for LLM-related failures.

**Subtypes:**
- `AuthenticationError`: Invalid API key or unauthorized access.
- `RateLimitError`: Provider rate limit exceeded (trigger for backoff retry).
- `ModelNotFoundError`: Requested model is unavailable or not found.
- `RegistryError`: Failure in provider registration or lookup.

### `ProviderRegistry` (Service)

The singleton registry that manages provider lifecycles.

**Core Methods:**
- `register(key, provider, enabled=True, description="")`: Adds a provider to the registry.
- `get(key, include_disabled=False)`: Retrieves a provider by key.
- `get_default()`: Returns the first enabled provider.
- `registry_status()`: Returns a summary of all registered providers.

---

## Appendix: Enums

### `AssetType`

| Value | Description |
|-------|-------------|
| `equity` | Common stocks, ADRs |
| `bond` | Fixed income and securities |
| `etf` | Exchange-traded funds |
| `crypto` | Digital assets (BTC, ETH, etc.) |
| `bond` | Fixed income and securities |
| `option` | Options and derivatives |
| `mutual_fund` | Actively managed funds |

### `TransactionType`

| Value | Description |
|-------|-------------|
| `buy` | Opening purchase |
| `sell` | Closing sale |
| ` tidak` | Internal transfer in/out |
| `dividend` | Cash distribution |
| `fee` | Account or transaction fee |
| `transfer` | Internal transfer in/out |

---

## Changelog

| Date | Commit | Change |
|------|--------|--------|
| 2026-05-15 | `05f0536` | Initial API: health, holdings CRUD, transactions CRUD, upload stub, review stub |
| 2026-05-17 | `chunk-1.1` | Added LLM Provider Registry (Base, Registry, OpenRouter) |
