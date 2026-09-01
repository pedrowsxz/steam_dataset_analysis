-- ============================================================================
-- infra/schema.sql
--
-- Postgres (Neon) schema for the Steam Gold-layer serving tables.
-- Idempotent: safe to run repeatedly (CREATE ... IF NOT EXISTS).
-- Source of truth for column shapes: databricks/03_build_gold_tables.sql
--
-- Apply with:
--   psql "$DATABASE_URL" -f infra/schema.sql
--
-- Neon requires SSL. That's enforced by the client connection string
-- (sslmode=require), not by anything in this file.
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- fact_games: one row per Steam appid (27,075 rows in Gold)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_games (
    appid                   INTEGER PRIMARY KEY,
    name                    TEXT NOT NULL,
    developer               TEXT,
    publisher               TEXT,
    release_date            DATE,                     -- 2 known NULLs in source
    release_year            SMALLINT,
    english                 BOOLEAN NOT NULL DEFAULT TRUE,
    required_age            SMALLINT NOT NULL DEFAULT 0,

    -- Deliberate deviation from the Gold DOUBLE type: money as NUMERIC avoids
    -- binary-float rounding drift on an aggregate (avg paid price) the API
    -- has to reproduce to the cent against the answer key.
    price                   NUMERIC(10, 2) NOT NULL DEFAULT 0,
    is_free                 BOOLEAN NOT NULL DEFAULT FALSE,
    price_tier              TEXT NOT NULL,

    positive_ratings        BIGINT NOT NULL DEFAULT 0,
    negative_ratings        BIGINT NOT NULL DEFAULT 0,
    total_ratings           BIGINT NOT NULL DEFAULT 0,
    positive_review_rate    DOUBLE PRECISION,          -- NULL when total_ratings = 0

    achievements             BIGINT NOT NULL DEFAULT 0,

    -- Owner counts are bucket-midpoint ESTIMATES, never exact figures. 2 known NULLs.
    owners_min               BIGINT,
    owners_max               BIGINT,
    owners_avg               BIGINT,

    has_windows              BOOLEAN NOT NULL DEFAULT TRUE,
    has_mac                  BOOLEAN NOT NULL DEFAULT FALSE,
    has_linux                BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT chk_price_tier CHECK (
        price_tier IN ('Free', 'Budget ($0.01-$4.99)', 'Standard ($5-$14.99)',
                        'Premium ($15-$29.99)', 'AAA ($30+)')
    ),
    CONSTRAINT chk_price_nonneg CHECK (price >= 0),
    CONSTRAINT chk_required_age_nonneg CHECK (required_age >= 0),
    CONSTRAINT chk_ratings_nonneg CHECK (positive_ratings >= 0 AND negative_ratings >= 0),
    CONSTRAINT chk_owners_order CHECK (
        owners_min IS NULL OR owners_max IS NULL OR owners_min <= owners_max
    )
);

CREATE INDEX IF NOT EXISTS idx_fact_games_release_year ON fact_games (release_year);
CREATE INDEX IF NOT EXISTS idx_fact_games_price_tier   ON fact_games (price_tier);
CREATE INDEX IF NOT EXISTS idx_fact_games_is_free      ON fact_games (is_free);

-- ----------------------------------------------------------------------------
-- game_genres: multi-label bridge table (76,462 rows; 85% of games have >1 genre)
--
-- Composite PK on (appid, genre) instead of a surrogate id: it's a natural
-- key, makes "duplicate genre tag for the same game" structurally
-- impossible, and needs no extra unique index.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS game_genres (
    appid   INTEGER NOT NULL REFERENCES fact_games (appid) ON DELETE CASCADE,
    genre   TEXT NOT NULL,
    PRIMARY KEY (appid, genre)
);

CREATE INDEX IF NOT EXISTS idx_game_genres_genre ON game_genres (genre);

-- ----------------------------------------------------------------------------
-- _export_runs: lineage/observability for every export_to_postgres.py run.
-- One row per attempt (success or failure), written by the script itself.
-- Leading underscore keeps it visually separate from the two serving tables
-- in any \dt listing or DB client.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS _export_runs (
    id                  BIGSERIAL PRIMARY KEY,
    started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at         TIMESTAMPTZ,
    source              TEXT NOT NULL,                 -- 'databricks' | 'csv_fallback' | 'parquet_fallback'
    status              TEXT NOT NULL DEFAULT 'running', -- 'running' | 'success' | 'failed'
    fact_games_rows     INTEGER,
    game_genres_rows    INTEGER,
    validation_passed   BOOLEAN,
    error_message       TEXT,

    CONSTRAINT chk_source CHECK (source IN ('databricks', 'csv_fallback', 'parquet_fallback')),
    CONSTRAINT chk_status CHECK (status IN ('running', 'success', 'failed'))
);

COMMIT;