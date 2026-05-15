# Omnifolio AI — Iterative Development Plan

> **Source of Truth for Development.** Every chunk is tiny, testable, and requires explicit approval before proceeding.
> Product spec lives in `QA_DISCUSSION.md` — this doc is the execution plan.

---

## Ground Rules

- **No big-bang merges.** Each chunk is a single PR with one clear scope.
- **Tests first, features second.** Red → Green → Refactor.
- **Every chunk must pass:** backend tests (`pytest`), frontend tests (`vitest`), type checks, manual browser smoke test, **AND `docker compose` verification**.
- **Git flow:** `main` is always deployable. Each chunk gets a feature branch → PR → approval → merge.
- **Docker-first verification:** Platform breaks things. Local-only testing is never sufficient. Every chunk is verified via `docker compose up` before being marked complete.
- **Nothing ships without explicit approval** from the product owner.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12+, FastAPI, Pydantic v2 |
| Frontend | Next.js 15 (App Router), TypeScript, React 19 |
| Styling | Tailwind CSS, CVA (class variance authority) |
| Charts | Recharts |
| Database | PostgreSQL + TimescaleDB |
| Migration | Alembic |
| Caching / Queue | Redis + Celery (deferred) |
| Testing (BE) | pytest + pytest-asyncio + httpx |
| Testing (FE) | vitest + @testing-library/react |
| Linting | ruff (Python), eslint (TS) |
| Docker | Multi-stage builds, docker compose |
| LLM Providers | OpenRouter (default) + OpenCode-Zen model |

---

## Approved Decisions

| Decision | Choice | Status |
|----------|--------|--------|
| LLM Provider (default) | **OpenRouter** | ✅ Approved |
| LLM Model | **openai/gpt-4o-mini** (swappable) | ✅ Approved |
| Mapper execution | **Synchronous on upload** | ✅ Approved |
| Sample data | **Realistic mock data** | ✅ Approved |
| Docker verification | **Every chunk verified via compose** | ✅ Approved |

---

## Phase 0: Foundation Rebuild

**Goal:** Project skeleton that builds, runs, and tests clean from zero. Docker is the verification platform.

### Chunk 0.1 — Directory Scaffolding ✅
- **Status:** 🟢 Completed — committed `b9bee01`
- **Deliverable:** Empty directory tree with `.gitkeep` files.

### Chunk 0.2 — Backend Configuration & Secrets ✅
- **Status:** 🟢 Completed — committed `004aa38`
- **Deliverable:** Config loads, all 22 tests pass, `/health` returns 200.

### Chunk 0.3 — Docker Infrastructure ✅
- **Status:** 🟢 Completed — committed `a3f8e2c`
- **In scope:** Dockerfiles + compose + init-db.sql
- Dockerfile.backend — multi-stage (builder + runtime), Python 3.12, uvicorn
- Dockerfile.frontend — multi-stage (builder + runtime), Node 20, Next.js
- docker-compose.yml — postgres, redis, backend, (frontend commented out)
- init-db.sql — holdings, transactions, ingestion_logs tables
- **Compose verification:** `docker compose up` starts all services. Backend `/health` returns 200.
- **Docker test verification:** `docker exec backend python -m pytest tests/` → **22/22 passed**

### Chunk 0.4 — Pydantic v2 Models ⬜
- Create `backend/app/models/__init__.py` with:
  - `AssetType` enum: `EQUITY`, `BOND`, `ETF`, `CRYPTO`, `OPTION`, `MUTUAL_FUND`
  - `HoldingBase` model: ticker (uppercase), quantity (>0), cost_basis (>=0, optional), asset_type
  - `Holding` extends HoldingBase: id (UUID), timestamps
  - `TransactionType` enum, `TransactionBase`, `Transaction`
  - `ColumnMapping` model for semantic mapper output
  - `IngestionResult` model: needs_review auto-sets via `@model_validator` when errors exist
  - `HealthCheck`, `ReadinessCheck`
- Create SQLAlchemy models: `backend/app/models/database_models.py`
- **Compose verification:** Build passes, import works inside container.
- **Status:** ⬜ Pending

### Chunk 0.5 — Backend Package Structure ⬜
- All `__init__.py` files, verify `from app.xxx import yyy` works.

### Chunk 0.6 — API Route Stubs ⬜
- FastAPI app, health, readiness, holdings CRUD, transactions CRUD, upload stubs.

### Chunk 0.7 — Frontend Scaffold ⬜
- Next.js 15 setup, tsconfig, tailwind, layout, homepage.

### Chunk 0.8 — Frontend Pages ⬜
- Upload, dashboard, review, not-found pages, Navbar.

### Chunk 0.9 — Frontend Components ⬜
- Card, UploadForm, ReviewTable, ConfidenceBadge, utils.

### Chunk 0.10 — All Tests Passing ⬜
- Full green suite: 39+ backend, 15+ frontend.

### Chunk 0.11 — Ruff & ESLint ⬜
- Zero lint errors.

---

**Phase 0 Gate:**
- [x] `docker compose up --build` starts without errors
- [x] Backend `GET /health` returns 200 inside container
- [x] Backend all tests pass inside container (22/22)
- [ ] Frontend homepage renders at `localhost:3001`
- [ ] Custom 404 page renders for unknown routes
- [ ] `ruff check .` passes clean
- [ ] `eslint .` passes clean

---

## Phase 1: AI Parser (MVP)

**Goal:** Upload a CSV or PDF → get structured, validated data back with a review UI.

### Chunk 1.1 — LLM Provider Registry
- `LLMProvider` ABC, `ProviderRegistry` singleton. OpenRouter + OpenCode-Zen default.
- **Compose verification:** Container can reach provider (mockable).

### Chunk 1.2 — Semantic Mapper
- `map_headers(headers, sample_rows)` → OpenRouter → column mapping JSON.
- **Compose verification:** Returns valid mapping for known patterns (mocked LLM).

### Chunk 1.3 — CSV Ingestion Pipeline
- CSV → parse → map → validate → `IngestionResult`.
- **Compose verification:** Known CSV → correct result.

### Chunk 1.4 — PDF Ingestion Pipeline
- PDF → Camelot → mapper → validate → `IngestionResult`. LLM fallback for failures.
- **Compose verification:** Known PDF → correct result.

### Chunk 1.5 — Upload Endpoint (Wired Up)
- `POST /upload` → file type detection → pipeline → result.
- **Compose verification:** Real file upload works end-to-end.

### Chunk 1.6 — Review & Confirm API
- `GET /review`, `POST /review/confirm`. IngestionLog model.
- **Compose verification:** Approve rows → stored in DB.

### Chunk 1.7 — Frontend Upload Page
- Drag-and-drop, status display, link to review.

### Chunk 1.8 — Frontend Review UI
- Table with approve/reject toggles, Confirm button.

### Chunk 1.9 — Error Handling & Edge Cases
- Global error handlers, 404/500 pages.

---

**Phase 1 Gate:**
- [ ] Upload CSV → mapped columns → approve → stored
- [ ] Upload PDF → extraction → review UI
- [ ] All tests pass inside Docker

---

## Phase 2: Ledger & Dashboard

### Chunk 2.1 — SQLAlchemy ORM Models
### Chunk 2.2 — CRUD Service Layer
### Chunk 2.3 — Dashboard API Endpoints
### Chunk 2.4 — Multi-Currency FX Layer
### Chunk 2.5 — Frontend Dashboard (Full)

---

**Phase 2 Gate:**
- [ ] Full demo: data persisted, dashboard works
- [ ] All tests pass inside Docker

---

## Phase 3: Provider Integrations

### Chunk 3.1 — BaseProvider Interface
### Chunk 3.2 — Broker Connector(s)

---

## Phase 4: Scaling & Deployment

### Chunk 4.1 — Production Docker Optimization
### Chunk 4.2 — CI/CD Pipeline

---

## Tracking

| # | Chunk | Status | Approved | Commit |
|---|-------|--------|----------|--------|
| 0.1 | Directory Scaffolding | ✅ Done | ✅ | `b9bee01` |
| 0.2 | Backend Config & Secrets | ✅ Done | ✅ | `004aa38` |
| 0.3 | Docker Infrastructure | ✅ Done | ✅ | `a3f8e2c` |
| 0.4 | Pydantic v2 Models | ⬜ Pending | ❌ | — |
| 0.5 | Backend Package Structure | ⬜ Pending | ❌ | — |
| 0.6 | API Route Stubs | ⬜ Pending | ❌ | — |
| 0.7 | Frontend Scaffold | ⬜ Pending | ❌ | — |
| 0.8 | Frontend Pages | ⬜ Pending | ❌ | — |
| 0.9 | Frontend Components | ⬜ Pending | ❌ | — |
| 0.10 | All Tests Passing | ⬜ Pending | ❌ | — |
| 0.11 | Ruff & ESLint | ⬜ Pending | ❌ | — |
| 1.1 | LLM Provider Registry | ⬜ Pending | ❌ | — |
| 1.2 | Semantic Mapper | ⬜ Pending | ❌ | — |
| 1.3 | CSV Pipeline | ⬜ Pending | ❌ | — |
| 1.4 | PDF Pipeline | ⬜ Pending | ❌ | — |
| 1.5 | Upload Endpoint Wired | ⬜ Pending | ❌ | — |
| 1.6 | Review & Confirm API | ⬜ Pending | ❌ | — |
| 1.7 | Frontend Upload Page | ⬜ Pending | ❌ | — |
| 1.8 | Frontend Review UI | ⬜ Pending | ❌ | — |
| 1.9 | Error Handling & Edge Cases | ⬜ Pending | ❌ | — |
| 2.1 | SQLAlchemy Models | ⬜ Pending | ❌ | — |
| 2.2 | CRUD Service Layer | ⬜ Pending | ❌ | — |
| 2.3 | Dashboard API | ⬜ Pending | ❌ | — |
| 2.4 | Multi-Currency FX Layer | ⬜ Pending | ❌ | — |
| 2.5 | Frontend Dashboard (Full) | ⬜ Pending | ❌ | — |
| 3.1 | BaseProvider Interface | ⬜ Pending | ❌ | — |
| 3.2 | Broker Connector(s) | ⬜ Pending | ❌ | — |
| 4.1 | Production Docker | ⬜ Pending | ❌ | — |
| 4.2 | CI/CD Pipeline | ⬜ Pending | ❌ | — |