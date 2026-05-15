-- Create tables for Omnifolio AI

CREATE TABLE IF NOT EXISTS holdings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL,
    ticker      VARCHAR(20) NOT NULL,
    quantity    NUMERIC(18, 8) NOT NULL CHECK (quantity > 0),
    cost_basis  NUMERIC(18, 2) CHECK (cost_basis >= 0),
    asset_type  VARCHAR(20) NOT NULL DEFAULT 'equity',
    currency    VARCHAR(3) DEFAULT 'USD',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL,
    ticker      VARCHAR(20) NOT NULL,
    txn_type    VARCHAR(20) NOT NULL CHECK (txn_type IN ('buy', 'sell', 'vest', 'dividend', 'deposit', 'withdrawal')),
    quantity    NUMERIC(18, 8) CHECK (quantity >= 0),
    price       NUMERIC(18, 2) CHECK (price >= 0),
    fees        NUMERIC(18, 2) NOT NULL DEFAULT 0 CHECK (fees >= 0),
    txn_date    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ingestion_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source          VARCHAR(100) NOT NULL,
    holdings_count  INTEGER NOT NULL DEFAULT 0,
    txn_count       INTEGER NOT NULL DEFAULT 0,
    errors          TEXT[],
    needs_review    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);