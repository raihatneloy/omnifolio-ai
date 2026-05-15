# Omnifolio AI — Q&A & Discussion Points

> Amended with project spec details. Canonical reference for architectural decisions.

---

## Architecture

### 1. Target Stack

**Python backend (FastAPI)** + **Next.js 15 (App Router)** frontend.
All frontend code is TypeScript; backend is Python 3.12+.
Unit tests from Day 1: `pytest` + `pytest-asyncio` for backend, `vitest` + `@testing-library/react` for frontend.
Git SCM from the first commit, Docker-based local dev environment.
Dashboards use **Recharts**; UI uses **Tailwind CSS** + **CVA**.

### 2. AI Provider Coupling

Multiple providers from the start. The `LLMProviderRegistry` pattern supports:
- **Google AI Studio** — default for cost efficiency
- **OpenRouter** — routes to multiple models for flexibility
- **OpenAI / Anthropic** — direct provider support

Interface: `generate(prompt, model) -> str`. Adding a provider = implementing one method. No vendor lock-in.

### 3. PDF Table Extraction

Hybrid approach:
1. **First pass:** `camelot-py[cv]` for table extraction (OpenCV backend).
2. **Fallback:** Multimodal LLM (GPT-4o via OpenRouter) for tables Camelot fails on.
3. **Validation:** Pydantic models enforce type safety; failed rows flagged for human review.

Camelot handles ~70-80% well. LLM fallback covers messy scans, merged cells. Cost stays manageable since LLM only sees failures.

---

## Data & Schema

### 4. Asset Ticker Standardization

- **US markets primary:** `AAPL`, `META`, `GOOGL` — bare ticker.
- **International:** exchange prefix — `LON:PCT` (London), `TSLA.DE` (Xetra), `7203.T` (TSE).
- Tickers normalized to **UPPERCASE** on ingestion.
- `provider_id` links back to source platform.
- Private equities / custom crypto handled via `asset_name` alongside ticker.

### 5. Multi-Currency & FX

- **Base currency: USD** — all raw values stored in USD.
- **User-selectable display currency** on dashboards.
- **Live FX rates** fetched at snapshot level for display conversion.
- Schema includes `currency` field per record; frontend handles display-time conversion.
- No rounding until final display layer.

---

## Business Model

### 6. Open Core Boundary

Self-hosted = **all features** (full AI parsing, reconciliation, dashboards).
Managed hosting (Pro tier) = **convenience + subsidized AI credits**.
No feature gating. License: **MIT** with commercial use exception.

### 7. Plugin Ecosystem

**Deferred.** Not in Phase 1-3 scope.
If requested post-launch, a `BaseProvider` interface with review process before listing.
Direct API integrations (Trading212, Tastytrade) built as first-class features, not plugins.

---

## Additional Decisions

### Mobile App
Not in Phase 1-3. Next.js frontend is responsive. React Native/Expo = Phase 4 consideration.

### Testing Strategy
- Every feature tested before merge.
- Backend: `pytest` + `pytest-asyncio` for async endpoints.
- Frontend: `vitest` + `@testing-library/react` for components and hooks.
- Integration tests verify LLM pipeline end-to-end with mocked API responses.
- CI runs full suite on every push.

### Version Control
- Git from Day 1. Feature branches, small PRs.
- Every chunk requires explicit code review and approval before merge.