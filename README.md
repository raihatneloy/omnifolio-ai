# Omnifolio AI

Privacy-first portfolio aggregator with AI-powered ingestion.

## Quick Start

```bash
# Copy env example
cp .env.example .env

# Start with Docker
docker compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:3001
```

## Features

- AI-powered CSV/PDF ingestion
- Multi-LLM support (OpenAI, Anthropic, Google AI Studio, OpenRouter)
- Portfolio dashboard with real-time FX
- Privacy-first, self-hostable

## Development

- Backend tests: `cd backend && pytest`
- Frontend tests: `cd frontend && npm test`
- See DEVELOPMENT_PLAN.md for iteration plan
