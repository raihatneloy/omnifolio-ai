# Omnifolio AI

Privacy-first portfolio aggregator with AI-powered ingestion.

## Quick Start

```bash
# Copy env example
cp .env.example .env

# Start with Docker
docker compose up --build

# Backend:  http://localhost:8000
# Frontend: http://localhost:3001
# API Docs: http://localhost:8000/docs  (Swagger UI)
```

## Features

- AI-powered CSV/PDF ingestion with multi-LLM support
- Portfolio dashboard with real-time FX conversion
- Privacy-first, self-hostable architecture

## Documentation

| Document | What it covers |
|----------|---------------|
| `API.md` | Full API reference (endpoints, request/response schemas, enums) |
| `DEVELOPMENT_PLAN.md` | Iteration plan (chunk-level roadmap, tracking table) |
| `QA_DISCUSSION.md` | Product spec and acceptance criteria |

## Development

```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test

# API reference
open API.md
```

## Architecture

```
Browser → Next.js (port 3001) → FastAPI (port 8000)
                                    ↓
                               PostgreSQL + Redis
```