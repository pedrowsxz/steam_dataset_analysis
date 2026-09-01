"""
export/export_to_postgres.py

Idempotent Gold-layer -> Neon Postgres loader.

Primary path : Databricks SQL Warehouse via databricks-sql-connector
Fallback path: local CSV/Parquet files exported from Databricks Gold tables,
               expected at:
                   {GOLD_EXPORT_DIR}/fact_games.(parquet|csv)
                   {GOLD_EXPORT_DIR}/game_genres.(parquet|csv)

Runs locally on demand. Not part of CI - CI never sees Neon or Databricks
credentials (see CI/CD plan, next phase).

Usage:
    python export/export_to_postgres.py [--source auto|databricks|files] [--dry-run]

Env vars (see infra/.env.example):
    DATABASE_URL          Neon connection string, sslmode=require (use the -pooler host)
    DATABRICKS_HOST
    DATABRICKS_TOKEN
    DATABRICKS_HTTP_PATH
    GOLD_EXPORT_DIR       default: data/gold_export
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from answer_key import EXPECTED_TOTAL_GAMES

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s %(message)s")
log = logging.getLogger("export")

REQUIRED_FACT_COLUMNS = [
    "appid", "name", "developer", "publisher", "release_date", "release_year",
    "english", "required_age", "price", "is_free", "price_tier",
    "positive_ratings", "negative_ratings", "total_ratings", "positive_review_rate",
    "achievements", "owners_min", "owners_max", "owners_avg",
    "has_windows", "has_mac", "has_linux",
]
REQUIRED_GENRE_COLUMNS = ["appid", "genre"]

Source = Literal["databricks", "csv_fallback", "parquet_fallback"]


@dataclass
class ExtractResult:
    fact_games: pd.DataFrame
    game_genres: pd.DataFrame
    source: Source


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def extract_from_databricks() -> ExtractResult:
    """Primary path. Raises on any failure; the caller decides whether to fall back."""
    from databricks import sql  # lazy import: package isn't needed for file-only runs

    host = os.environ["DATABRICKS_HOST"]
    token = os.environ["DATABRICKS_TOKEN"]
    http_path = os.environ["DATABRICKS_HTTP_PATH"]

    log.info("Connecting to Databricks SQL warehouse at %s", host)
    with sql.connect(server_hostname=host, http_path=http_path, access_token=token) as conn:
        fact_games = pd.read_sql("SELECT * FROM workspace.gold.fact_games", conn)
        game_genres = pd.read_sql("SELECT * FROM workspace.gold.game_genres", conn)

    return ExtractResult(fact_games, game_genres, source="databricks")


def extract_from_files() -> ExtractResult:
    """Fallback path: CSV or Parquet exports sitting in GOLD_EXPORT_DIR."""
    export_dir = Path(os.environ.get("GOLD_EXPORT_DIR", "data/gold_export"))

    def _load(stem: str) -> tuple[pd.DataFrame, Source]:
        parquet_path = export_dir / f"{stem}.parquet"
        csv_path = export_dir / f"{stem}.csv"
        if parquet_path.exists():
            return pd.read_parquet(parquet_path), "parquet_fallback"
        if csv_path.exists():
            return pd.read_csv(csv_path), "csv_fallback"
        raise FileNotFoundError(
            f"Neither {parquet_path} nor {csv_path} exists. "
            "Export the Gold tables from a Databricks notebook first "
            "(see docs/data_dictionary.md) and place them under GOLD_EXPORT_DIR."
        )

    fact_games, fact_source = _load("fact_games")
    game_genres, _ = _load("game_genres")
    return ExtractResult(fact_games, game_genres, source=fact_source)


def extract(preferred: str) -> ExtractResult:
    if preferred == "files":
        return extract_from_files()
    if preferred == "databricks":
        return extract_from_databricks()

    # auto: try Databricks, fall back to files on ANY failure - missing creds,
    # a cold/quota-exhausted SQL warehouse, network egress restrictions, etc.
    try:
        return extract_from_databricks()
    except Exception as exc:  # noqa: BLE001 - intentionally broad: any failure -> fallback
        log.warning("Databricks extraction failed (%s: %s) - falling back to local files",
                    type(exc).__name__, exc)
        return extract_from_files()


# ---------------------------------------------------------------------------
# Validation (pre-load gate: cheap structural checks. The full answer-key
# comparison against known aggregates lives in validate_load.py and runs
# AFTER the load.)
# ---------------------------------------------------------------------------

def validate_source(result: ExtractResult) -> None:
    fact, genres = result.fact_games, result.game_genres

    missing_fact = set(REQUIRED_FACT_COLUMNS) - set(fact.columns)
    missing_genre = set(REQUIRED_GENRE_COLUMNS) - set(genres.columns)
    if missing_fact:
        raise ValueError(f"fact_games missing columns: {sorted(missing_fact)}")
    if missing_genre:
        raise ValueError(f"game_genres missing columns: {sorted(missing_genre)}")

    if fact["appid"].isna().any():
        raise ValueError("fact_games has NULL appid values (primary key cannot be null)")
    if fact["appid"].duplicated().any():
        dupes = fact.loc[fact["appid"].duplicated(), "appid"].tolist()[:10]
        raise ValueError(f"fact_games has duplicate appid values, e.g. {dupes}")

    orphaned = set(genres["appid"]) - set(fact["appid"])
    if orphaned:
        raise ValueError(
            f"game_genres references {len(orphaned)} appid(s) not in fact_games, "
            f"e.g. {list(orphaned)[:10]}"
        )

    if len(fact) < EXPECTED_TOTAL_GAMES * 0.95:
        raise ValueError(
            f"fact_games has only {len(fact)} rows, expected ~{EXPECTED_TOTAL_GAMES}. "
            "Refusing to load a suspiciously small dataset - check the source export."
        )

    log.info("Source validated: %d games, %d genre rows", len(fact), len(genres))


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def get_engine() -> Engine:
    database_url = os.environ["DATABASE_URL"]
    # Neon requires SSL. Belt-and-braces: enforce it even if the URL forgot it.
    connect_args = {"sslmode": "require"} if "sslmode=" not in database_url else {}
    return create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)


def load(engine: Engine, result: ExtractResult) -> tuple[int, int]:
    """TRUNCATE + reload inside a single transaction: all-or-nothing, and the
    right idempotency strategy for a static historical dataset (no need for
    row-level upsert/merge complexity)."""
    fact = result.fact_games[REQUIRED_FACT_COLUMNS]
    genres = result.game_genres[REQUIRED_GENRE_COLUMNS]

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE game_genres, fact_games RESTART IDENTITY CASCADE"))
        fact.to_sql("fact_games", conn, if_exists="append", index=False, method="multi", chunksize=1000)
        genres.to_sql("game_genres", conn, if_exists="append", index=False, method="multi", chunksize=2000)

        fact_count = conn.execute(text("SELECT COUNT(*) FROM fact_games")).scalar_one()
        genre_count = conn.execute(text("SELECT COUNT(*) FROM game_genres")).scalar_one()

        if fact_count != len(fact) or genre_count != len(genres):
            raise RuntimeError(
                f"Row-count mismatch after load: fact_games {fact_count}/{len(fact)}, "
                f"game_genres {genre_count}/{len(genres)}. Rolling back."
            )

    return fact_count, genre_count


def start_run(engine: Engine, source: str) -> int:
    with engine.begin() as conn:
        return conn.execute(
            text("INSERT INTO _export_runs (source, status) VALUES (:source, 'running') RETURNING id"),
            {"source": source},
        ).scalar_one()


def finish_run(engine: Engine, run_id: int, *, status: str, fact_rows: int | None = None,
                genre_rows: int | None = None, validation_passed: bool | None = None,
                error_message: str | None = None) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE _export_runs
                SET status = :status,
                    finished_at = now(),
                    fact_games_rows = :fact_rows,
                    game_genres_rows = :genre_rows,
                    validation_passed = :validation_passed,
                    error_message = :error_message
                WHERE id = :run_id
                """
            ),
            dict(status=status, fact_rows=fact_rows, genre_rows=genre_rows,
                 validation_passed=validation_passed, error_message=error_message, run_id=run_id),
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Load Steam Gold tables into Neon Postgres.")
    parser.add_argument("--source", choices=["auto", "databricks", "files"], default="auto",
                         help="Where to read Gold data from. 'auto' tries Databricks then falls back to files.")
    parser.add_argument("--dry-run", action="store_true",
                         help="Extract and validate only; skip writing to Postgres.")
    args = parser.parse_args()

    try:
        result = extract(args.source)
        validate_source(result)
    except Exception as exc:
        log.error("Extraction/validation failed: %s", exc)
        return 1

    if args.dry_run:
        log.info("--dry-run set: skipping Postgres load. source=%s fact=%d rows genres=%d rows",
                  result.source, len(result.fact_games), len(result.game_genres))
        return 0

    engine = get_engine()
    run_id = start_run(engine, source=result.source)
    try:
        fact_count, genre_count = load(engine, result)
        finish_run(engine, run_id, status="success", fact_rows=fact_count, genre_rows=genre_count,
                   validation_passed=True)
        log.info("Loaded %d fact_games rows and %d game_genres rows from %s",
                  fact_count, genre_count, result.source)
        log.info("Next: python export/validate_load.py")
        return 0
    except Exception as exc:
        finish_run(engine, run_id, status="failed", error_message=str(exc)[:2000])
        log.error("Load failed and was rolled back: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())