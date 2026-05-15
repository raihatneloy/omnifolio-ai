# Omnifolio AI — Iterative Development Plan

> **Source of Truth for Development.** Every chunk is tiny, testable, and requires explicit approval before proceeding.
> Product spec lives in `QA_DISCUSSION.md` — this doc is the execution plan.

---

## Ground Rules

- **No big-bang merges.** Each chunk is a single PR with one clear scope.
- **Tests first, features second.** Red → Green → Refactor.
- **Every chunk must pass:** backend tests (`pytest`), frontend tests (`vitest`), type checks, and manual browser smoke test.
- **Git flow:** `main` is always deployable. Each chunk gets a feature branch → PR → approval → merge.
- **Docker dev environment must work** at the end of every phase.
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
| Caching / Queue | Redis + Celery |
| Testing (BE) | pytest + pytest-asyncio + httpx |
| Testing (FE) | vitest + @testing-library/react |
| Linting | ruff (Python), eslint (TS) |
| Docker | Multi-stage builds, docker compose |
| LLM Providers | OpenRouter (default), Google AI Studio, OpenAI, Anthropic |

---

## Phase 0: Foundation Rebuild

**Goal:** Project skeleton that builds, runs, and tests clean from zero.

### Chunk 0.1 — Directory Scaffolding
- Create top-level directory structure:
  ```
  omnifolio-ai/
  ├── backend/
  │   ├── app/
  │   │   ├── api/
  │   │   ├── core/
  │   │   ├── ingestion/
  │   │   ├── models/
  │   │   ├── routes/
  │   │   ├── services/
  │   │   ├── __init__.py
  │   │   └── main.py
  │   ├── tests/
  │   ├── docker/
  │   ├── pyproject.toml
  │   ├── requirements.txt
  │   └── .pytest_cache/
  ├── frontend/
  │   ├── app/
  │   │   ├── components/
  │   │   ├── lib/
  │   │   ├── globals.css
  │   │   ├── layout.tsx
  │   │   ├── page.tsx
  │   │   └── not-found.tsx
  │   ├── public/
  │   ├── tests/
  │   ├── next.config.js
  │   ├── package.json
  │   ├── tsconfig.json
  │   ├── tailwind.config.ts
  │   └── vitest.config.ts
  ├── docker/
  │   ├── Dockerfile.backend
  │   ├── Dockerfile.frontend
  │   ├── docker-compose.yml
  │   └── init-db.sql
  ├── .github/workflows/
  ├── .gitignore
  ├── .env.example
  ├── README.md
  ├── DEVELOPMENT_PLAN.md
  ├── QA_DISCUSSION.md
```

### Chunk 0.1 — Directory Scaffolding ✅
- **Status:** 🟢 Completed — committed `b9bee01`
- **Deliverable:** Empty directory tree with `.gitkeep` files where needed.

### Chunk 0.2 — Backend Configuration & Secrets
- Create `backend/app/core/config.py` using Pydantic `BaseSettings`:
  - `DATABASE_URL` (PostgreSQL)
  - `REDIS_URL`
  - `SECRET_KEY`
  - `LLM_PROVIDER` (default: `"openrouter"`)
  - `LLM_API_KEY`
  - `ENV` (development/production)
- Create `.env.example` with all variables documented and placeholder values.
- **Deliverable:** Config loads without errors; missing env vars raise clear errors.
- **Test:** Import `get_settings()` and verify defaults; write test that fails gracefully on missing required vars.

### Chunk 0.3 — Database Layer
- Create `backend/app/core/database.py`:
  - Async engine creation with `asyncpg`
  - Session dependency for FastAPI
  - `init_db()` function for tables
- Create `backend/docker/init-db.sql`:
  - Create `holdings` table (id, ticker, quantity, cost_basis, asset_type, created_at, updated_at)
  - Create `transactions` table (id, ticker, txn_type, quantity, price, fees, txn_date, notes, created_at)
  - Create `ingestion_logs` table (id, source, holdings_count, transactions_count, errors, needs_review, created_at)
- **Deliverable:** `docker compose up` starts PostgreSQL; `init-db.sql` runs successfully.
- **Test:** Connect to DB from Python, run a simple query.

### Chunk 0.4 — Pydantic v2 Models
- Create `backend/app/models/__init__.py`:
  - `AssetType` enum: `EQUITY`, `BOND`, `ETF`, `CRYPTO`, `OPTION`, `MUTUAL_FUND`
  - `HoldingBase` model: ticker (normalized to uppercase), quantity (>0), cost_basis (>=0, optional), asset_type
  - `HoldingCreate` extends HoldingBase
  - `Holding` extends HoldingBase: id (UUID), created_at, updated_at, `from_attributes = True`
  - `TransactionType` enum: `BUY`, `SELL`, `VEST`, `DIVIDEND`, `DEPOSIT`, `WITHDRAWAL`
  - `TransactionBase` model: ticker, txn_type, quantity (optional), price (optional), fees, txn_date, notes
  - `TransactionCreate` extends TransactionBase
  - `Transaction` extends TransactionBase: id (UUID), created_at
  - `IngestionResult` model: source, holdings_ingested, transactions_ingested, errors (list), needs_review (auto-set via `@model_validator` if errors exist), confidence (property), success (property)
  - `HealthCheck` model: status, version, database, redis
  - `ReadinessCheck` model: ready, services dict
- **Deliverable:** All models import cleanly, validation works, tests pass.
- **Test:** Test each model with valid data, invalid data (negative quantity, missing ticker), and verify `needs_review` auto-sets when errors are present.

### Chunk 0.5 — Backend Package Structure
- Create all `__init__.py` files:
  - `backend/app/__init__.py`
  - `backend/app/core/__init__.py`
  - `backend/app/api/__init__.py`
  - `backend/app/models/__init__.py` (from Chunk 0.4)
  - `backend/app/ingestion/__init__.py`
  - `backend/app/routes/__init__.py`
  - `backend/app/services/__init__.py`
- **Deliverable:** `from app.models import Holding` works from anywhere in the project.
- **Test:** Import chain succeeds; no circular imports.

### Chunk 0.6 — API Route Stubs
- Create `backend/app/main.py` — FastAPI app with CORS, title, version.
- Create `backend/app/api/health.py`:
  - `GET /health` → returns `{"status": "ok"}` (200)
- Create `backend/app/api/readiness.py`:
  - `GET /ready` → checks DB + Redis connections, returns `ReadinessCheck`
- Create `backend/app/api/holdings.py`:
  - `GET /holdings` → list all holdings (empty list stub)
  - `GET /holdings/{id}` → get one (404 stub)
  - `POST /holdings` → create holding (validation stub)
  - `DELETE /holdings/{id}` → delete (stub)
- Create `backend/app/api/transactions.py`:
  - `GET /transactions` → list all (empty list stub)
  - `POST /transactions` → create transaction (validation stub)
- Create `backend/app/api/upload.py`:
  - `POST /upload` → accept file upload (stub, returns placeholder)
- Include all routes in `main.py` via `include_router()`.
- **Deliverable:** All endpoints return at least a 200 or proper 4xx with JSON.
- **Test:** Hit every endpoint with `httpx.AsyncClient`, verify status codes and response shapes.

### Chunk 0.7 — Frontend Scaffold
- Initialize Next.js 15 project:
  - `npx create-next-app@latest` with TypeScript, Tailwind, App Router.
- Configure `tsconfig.json` with strict mode.
- Configure `tailwind.config.ts` and `globals.css`.
- Create `app/layout.tsx` — root layout with metadata, fonts, Tailwind import.
- Create `app/page.tsx` — homepage with project title and navigation links.
- Create `app/globals.css` — base styles, dark theme.
- **Deliverable:** `npm run dev` starts on `localhost:3000`, homepage renders.
- **Test:** Vitest setup, smoke test that homepage renders `<h1>`.

### Chunk 0.8 — Frontend Pages
- Create `app/upload/page.tsx` — file upload form (drag-and-drop zone, submit button, status display).
- Create `app/dashboard/page.tsx` — dashboard skeleton (holdings summary, allocation chart placeholder, recent transactions table).
- Create `app/review/page.tsx` — review page skeleton (table with approve/reject toggles).
- Create `app/not-found.tsx` — custom 404 page with helpful message and navigation.
- Create `app/components/Navbar.tsx` — navigation bar with links to Home, Upload, Dashboard, Review.
- **Deliverable:** All pages render without 404; navigation works via Next.js Link.
- **Test:** Each page renders, Navbar links navigate (no 404).

### Chunk 0.9 — Frontend Components
- Create `app/components/ui/card.tsx` — reusable card component (CVA-based variants).
- Create `app/components/UploadForm.tsx` — file input + submit + status.
- Create `app/components/ReviewTable.tsx` — table with approve/reject toggles per row.
- Create `app/components/ConfidenceBadge.tsx` — color-coded badge for confidence scores.
- Create `app/lib/utils.ts` — shared utility functions (date formatting, currency formatting).
- **Deliverable:** Components import and render in Storybook-style or test environment.
- **Test:** Component render tests with mocked props.

### Chunk 0.10 — Docker Setup
- Create `docker/Dockerfile.backend` — multi-stage build (builder + runtime), Python 3.12, uvicorn.
- Create `docker/Dockerfile.frontend` — multi-stage Node build.
- Create `docker/docker-compose.yml` — backend, frontend, postgres, redis services with proper networking, volumes, health checks.
- Create `docker/init-db.sql` — schema initialization.
- **Deliverable:** `docker compose up --build` starts everything. Backend health returns 200. Frontend serves homepage.
- **Test:** Manual smoke test — open browser, navigate to both services, verify connectivity.

### Chunk 0.11 — All Tests Passing
- Write all missing backend tests to cover Chunks 0.2–0.6.
- Write all missing frontend tests to cover Chunks 0.7–0.9.
- Fix all failures, ensure full green suite.
- **Deliverable:** 39+ backend tests pass, 15+ frontend tests pass.
- **Test:** `cd backend && pytest` → all green. `cd frontend && npm test` → all green.

### Chunk 0.12 — Ruff & ESLint Configuration
- Configure `ruff.toml` for backend — fix all linting errors.
- Configure `.eslintrc.json` for frontend — fix all linting errors.
- Add pre-commit hook (optional, via `ruff check` and `eslint`).
- **Deliverable:** `ruff check .` and `eslint .` both pass clean.
- **Test:** Run both linters, zero errors.

---

**Phase 0 Gate:**
- [ ] `docker compose up --build` starts without errors
- [ ] Backend `GET /health` returns 200 with `{"status": "ok"}`
- [ ] Backend `GET /ready` returns 200 with all services healthy
- [ ] Frontend homepage renders at `localhost:3001`
- [ ] All 39+ backend tests pass
- [ ] All 15+ frontend tests pass
- [ ] `ruff check .` passes clean
- [ ] `eslint .` passes clean
- [ ] Custom 404 page renders for unknown routes

---

## Phase 1: AI Parser (MVP)

**Goal:** Upload a CSV or PDF → get structured, validated data back with a review UI.

### Chunk 1.1 — LLM Provider Registry
- Create `backend/app/services/llm_provider.py`:
  - `LLMProvider` abstract base class with `generate(prompt: str, model: str) -> str`.
  - `OpenRouterProvider` implementation — uses OpenRouter API, default model: `openai/gpt-4o`.
  - `GoogleAIStudioProvider` implementation.
  - `OpenAIProvider` implementation.
  - `AnthropicProvider` implementation.
  - `ProviderRegistry` singleton — register, get, list providers.
  - Default provider reads from `config.py` settings.
- **Deliverable:** `registry.get("openrouter").generate("Hello")` returns a response.
- **Test:** Mock HTTP calls, verify correct API endpoint/headers/payloads for each provider.

### Chunk 1.2 — Semantic Mapper
- Create `backend/app/ingestion/semantic_mapper.py`:
  - Function `map_headers(headers: list[str], sample_rows: list[dict], provider: str) -> dict`:
    - Sends header names + sample rows to LLM.
    - Prompts for mapping CSV columns → universal schema fields (ticker, quantity, cost_basis, txn_type, price, date, etc.).
    - Returns validated JSON mapping via Pydantic model `ColumnMapping`.
  - Handles common variations (e.g., "Ticker" → "ticker", "Symbol" → "ticker", "Qty" → "quantity").
  - Fallback: if LLM returns invalid JSON, retry with simpler prompt.
- **Deliverable:** Given a list of headers, returns a valid `ColumnMapping` dict.
- **Test:** Test with 5+ known header patterns (TD Ameritrade, Schwab, Fidelity, IBKR, generic). Mock LLM response.

### Chunk 1.3 — CSV Ingestion Pipeline
- Create `backend/app/ingestion/csv_pipeline.py`:
  - Function `ingest_csv(file_content: bytes, filename: str, provider: str) -> IngestionResult`:
    1. Parse CSV via `csv.DictReader`.
    2. Call Semantic Mapper to get column mapping.
    3. Apply mapping to extract holdings/transactions.
    4. Validate each row via Pydantic models.
    5. Collect errors per row.
    6. Return `IngestionResult` with counts, errors, needs_review flag.
  - Handle encoding issues (UTF-8, Latin-1).
  - Handle empty files gracefully.
- **Deliverable:** Upload a CSV → get structured, validated `IngestionResult` back.
- **Test:** Test with 3+ sample CSVs (mock CSV content), verify correct parsing, error collection, and `needs_review` behavior.

### Chunk 1.4 — PDF Ingestion Pipeline
- Create `backend/app/ingestion/pdf_pipeline.py`:
  - Function `ingest_pdf(file_content: bytes, filename: str, provider: str) -> IngestionResult`:
    1. Try Camelot table extraction first.
    2. If Camelot fails or returns empty → fallback to sending page screenshots to multimodal LLM via OpenRouter.
    3. Pass extracted data through Semantic Mapper.
    4. Validate via Pydantic.
    5. Return `IngestionResult`.
  - Log which extraction method was used.
- **Deliverable:** Upload a PDF → get structured result. Camelot path tested separately from LLM fallback path.
- **Test:** Test Camelot path with mocked table data. Test fallback path with mocked LLM response.

### Chunk 1.5 — Upload Endpoint (Wired Up)
- Update `backend/app/api/upload.py`:
  - Accept `POST /upload` with `multipart/form-data` file.
  - Detect file type (CSV vs PDF) by extension and content.
  - Route to appropriate pipeline.
  - Return `IngestionResult` JSON.
- Wire up LLM provider config.
- **Deliverable:** Real file upload works end-to-end (with mocked LLM).
- **Test:** Upload CSV → verify response JSON structure. Upload PDF → verify response. Test with invalid file type.

### Chunk 1.6 — Review & Confirm API
- Update `backend/app/api/upload.py` (or create new `review.py`):
  - `POST /review/confirm` — accept list of confirmed holdings/transactions, persist to DB.
  - `GET /review/{ingestion_id}` — retrieve ingestion result with per-row status.
- Add `IngestionLog` SQLAlchemy model (id, source, holdings_count, transactions_count, errors, needs_review, created_at).
- **Deliverable:** User can approve rows → confirmed data stored in DB.
- **Test:** Confirm endpoint stores data. Read endpoint retrieves it.

### Chunk 1.7 — Frontend Upload Page (Functional)
- Update `app/upload/page.tsx`:
  - File drag-and-drop zone.
  - File type detection, submit button.
  - Status: uploading → processing → done.
  - Display `IngestionResult` summary (counts, errors, needs_review).
  - Link to review page if `needs_review` is true.
- **Deliverable:** Upload form works end-to-end with mock API.
- **Test:** Component renders, file selection triggers upload, result displays.

### Chunk 1.8 — Frontend Review UI
- Update `app/review/page.tsx`:
  - Table of parsed rows with columns: Ticker, Quantity, Cost Basis, Type, Status, Actions.
  - Each row has Approve / Reject toggle.
  - "Confirm Selection" button sends confirmed rows to API.
  - `ConfidenceBadge` component shows color-coded confidence per row.
- **Deliverable:** Review page renders rows, toggles work, confirm button sends data.
- **Test:** Component renders with mock data, toggle changes state, confirm triggers API call.

### Chunk 1.9 — Error Handling & Edge Cases
- Add global error handler in FastAPI (`@app.exception_handler`).
- Add validation error responses with structured JSON.
- Handle: empty files, unsupported file types, LLM timeouts, DB connection failures.
- Add user-friendly error pages on frontend (404, 500).
- **Deliverable:** Graceful error handling everywhere.
- **Test:** Force each error condition, verify proper response.

---

**Phase 1 Gate:**
- [ ] Upload a CSV → see mapped columns → approve rows → data stored in DB
- [ ] Upload a PDF → Camelot extraction works (or LLM fallback) → review UI works
- [ ] All new backend tests pass
- [ ] All new frontend tests pass
- [ ] Custom error pages render for 404/500

---

## Phase 2: Ledger & Dashboard

### Chunk 2.1 — SQLAlchemy ORM Models
- Create `backend/app/models/database_models.py`:
  - `HoldingModel` (SQLAlchemy): id, user_id, ticker, quantity, cost_basis, asset_type, created_at, updated_at.
  - `TransactionModel` (SQLAlchemy): id, user_id, ticker, txn_type, quantity, price, fees, txn_date, notes, created_at.
  - `IngestionLogModel` (SQLAlchemy): id, source, holdings_count, txn_count, errors, needs_review, created_at.
- Write Alembic migration (`alembic init`, `alembic revision --autogenerate`).
- **Deliverable:** Models map to existing DB tables. Alembic can upgrade/downgrade.
- **Test:** Create, read, update, delete via SQLAlchemy session.

### Chunk 2.2 — CRUD Service Layer
- Create `backend/app/services/services.py`:
  - `HoldingService`: create, get_by_id, list_all, delete.
  - `TransactionService`: create, get_by_id, list_all.
  - `IngestionLogService`: create, get_by_id, list_recent.
- Each service method has proper error handling (not found, validation).
- **Deliverable:** Services callable from API routes via FastAPI dependency injection.
- **Test:** Full CRUD test coverage for each service.

### Chunk 2.3 — Dashboard API Endpoints
- Create `backend/app/api/dashboard.py`:
  - `GET /dashboard/holdings` → list all holdings with calculated totals.
  - `GET /dashboard/summary` → portfolio summary (total value, allocation by type, etc.).
  - `GET /dashboard/transactions` → paginated transaction list.
- **Deliverable:** Dashboard data available via API.
- **Test:** API returns correct data shapes for each endpoint.

### Chunk 2.4 — Dashboard Frontend
- Update `app/dashboard/page.tsx`:
  - Holdings summary cards (total value, number of positions, asset type breakdown).
  - Allocation chart using Recharts (`PieChart`).
  - Recent transactions table.
- **Deliverable:** Dashboard renders real data from API.
- **Test:** Component renders with mock API data.

### Chunk 2.5 — Multi-Currency FX Layer
- Create `backend/app/services/fx_service.py`:
  - Fetch live FX rates from free API (exchangerate-api.com or similar).
  - Cache rates in Redis for 1 hour.
  - Convert amounts between currencies.
- Add `currency` field to Holding/Transaction models.
- **Deliverable:** Holdings stored with currency, displayable in any currency via FX conversion.
- **Test:** FX fetch works (or mock), caching works, conversion is accurate.

---

**Phase 2 Gate:**
- [ ] Full working demo: data persisted, dashboard shows holdings + charts + transactions
- [ ] All new tests pass
- [ ] Docker compose still starts cleanly
- [ ] FX conversion works end-to-end

---

## Phase 3: Provider Integrations

### Chunk 3.1 — BaseProvider Interface
- Define `BaseProvider` ABC in `backend/app/services/providers/base.py`:
  - `fetch_holdings(account_id: str) -> list[Holding]`
  - `fetch_transactions(account_id: str, start: datetime, end: datetime) -> list[Transaction]`
  - `validate_connection() -> bool`
- **Deliverable:** Abstract interface defined, cannot be instantiated directly.
- **Test:** Test that instantiation raises, test subclass requirements.

### Chunk 3.2 — Broker Connector(s)
- Implement first connector (e.g., Interactive Brokers CSV export parser, or a mock broker for dev).
- Register in `ProviderRegistry`.
- **Deliverable:** Data from broker export can be fetched through `BaseProvider` interface.
- **Test:** Integration test with sample broker data.

---

## Phase 4: Scaling & Deployment

### Chunk 4.1 — Production Docker Optimization
- Multi-stage builds for smaller images.
- Gunicorn + Uvicorn workers for backend.
- Nginx for frontend static files.
- Health checks in compose.
- Graceful shutdown handling.
- **Deliverable:** Production-ready images, `docker compose -f docker-compose.prod.yml up`.
- **Test:** Image sizes under threshold, health checks pass, graceful shutdown verified.

### Chunk 4.2 — CI/CD Pipeline
- `.github/workflows/ci.yml`:
  - Lint (ruff + eslint).
  - Type check (mypy + tsc).
  - Test (pytest + vitest).
  - Build Docker images.
  - Deploy on merge to main (optional: GitHub Pages for frontend preview).
- **Deliverable:** Push to any branch triggers CI, merge to main deploys.
- **Test:** CI runs cleanly on a test PR.

---

## Tracking

| Chunk | Status | Approved? |
|-------|--------|-----------|
| 0.1 Directory Scaffolding | 🟢 Completed | ✅ | `b9bee01` |
| 0.2 Backend Config & Secrets | ⬜ Not started | ❌ |
| 0.3 Database Layer | ⬜ Not started | ❌ |
| 0.4 Pydantic v2 Models | ⬜ Not started | ❌ |
| 0.5 Backend Package Structure | ⬜ Not started | ❌ |
| 0.6 API Route Stubs | ⬜ Not started | ❌ |
| 0.7 Frontend Scaffold | ⬜ Not started | ❌ |
| 0.8 Frontend Pages | ⬜ Not started | ❌ |
| 0.9 Frontend Components | ⬜ Not started | ❌ |
| 0.10 Docker Setup | ⬜ Not started | ❌ |
| 0.11 All Tests Passing | ⬜ Not started | ❌ |
| 0.12 Ruff & ESLint | ⬜ Not started | ❌ |
| 1.1 LLM Provider Registry | ⬜ Not started | ❌ |
| 1.2 Semantic Mapper | ⬜ Not started | ❌ |
| 1.3 CSV Pipeline | ⬜ Not started | ❌ |
| 1.4 PDF Pipeline | ⬜ Not started | ❌ |
| 1.5 Upload Endpoint Wired | ⬜ Not started | ❌ |
| 1.6 Review & Confirm API | ⬜ Not started | ❌ |
| 1.7 Frontend Upload Page | ⬜ Not started | ❌ |
| 1.8 Frontend Review UI | ⬜ Not started | ❌ |
| 1.9 Error Handling & Edge Cases | ⬜ Not started | ❌ |
| 2.1 SQLAlchemy Models | ⬜ Not started | ❌ |
| 2.2 CRUD Service Layer | ⬜ Not started | ❌ |
| 2.3 Dashboard API | ⬜ Not started | ❌ |
| 2.4 Dashboard Frontend | ⬜ Not started | ❌ |
| 2.5 Multi-Currency FX Layer | ⬜ Not started | ❌ |
| 3.1 BaseProvider Interface | ⬜ Not started | ❌ |
| 3.2 Broker Connector(s) | ⬜ Not started | ❌ |
| 4.1 Production Docker | ⬜ Not started | ❌ |
| 4.2 CI/CD Pipeline | ⬜ Not started | ❌ |