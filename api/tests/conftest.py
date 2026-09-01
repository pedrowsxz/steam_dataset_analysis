"""
api/tests/conftest.py

Integration tests against a REAL Postgres instance. The schema and routers
use Postgres-specific SQL (FILTER, CORR, ::numeric casts) with no sqlite
equivalent, so mocking the DB isn't worth the fidelity loss.

Point DATABASE_URL at any throwaway Postgres 15+ instance before running
pytest — a local Docker container, a GitHub Actions service container, or a
scratch branch. NEVER point this at the production database: the schema is
(re)applied and ALL data in the target database is replaced with a small
fixture on every test session.

    docker run -d --name steam-test-db -e POSTGRES_PASSWORD=postgres \
        -e POSTGRES_DB=steam_test -p 5433:5432 postgres:16
    export DATABASE_URL=postgresql://postgres:postgres@localhost:5433/steam_test
    cd api && pytest

This fixture is small (6 games) and hand-computable on purpose — it exercises
every endpoint's logic (multi-genre percentages, fixed tier ordering, the
2019 partial-year YoY-null rule, platform breakdowns, scatter sampling)
without needing the real 27,075-row dataset. The FULL answer-key numbers in
export/answer_key.py only hold against a real production load; those get
checked separately by export/validate_load.py after an actual export run.
"""
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:5173")

if not os.environ.get("DATABASE_URL"):
    raise RuntimeError(
        "Set DATABASE_URL to a throwaway Postgres instance before running these tests. "
        "See the docstring at the top of api/tests/conftest.py."
    )

SCHEMA_SQL_PATH = Path(__file__).resolve().parents[2] / "infra" / "schema.sql"

FIXTURE_GAMES = [
    dict(appid=1, name="Free Sample", developer="Dev A", publisher="Pub A",
         release_date="2016-01-01", release_year=2016, price=0.00, is_free=True,
         price_tier="Free", positive_ratings=50, negative_ratings=50, total_ratings=100,
         positive_review_rate=0.50, has_windows=True, has_mac=False, has_linux=False),
    dict(appid=2, name="Budget Buy", developer="Dev A", publisher="Pub A",
         release_date="2017-03-01", release_year=2017, price=3.99, is_free=False,
         price_tier="Budget ($0.01-$4.99)", positive_ratings=80, negative_ratings=20, total_ratings=100,
         positive_review_rate=0.80, has_windows=True, has_mac=True, has_linux=False),
    dict(appid=3, name="Mid Tier", developer="Dev B", publisher="Pub B",
         release_date="2017-06-01", release_year=2017, price=9.99, is_free=False,
         price_tier="Standard ($5-$14.99)", positive_ratings=60, negative_ratings=40, total_ratings=100,
         positive_review_rate=0.60, has_windows=True, has_mac=False, has_linux=False),
    dict(appid=4, name="Premium One", developer="Dev B", publisher="Pub B",
         release_date="2018-02-01", release_year=2018, price=19.99, is_free=False,
         price_tier="Premium ($15-$29.99)", positive_ratings=90, negative_ratings=10, total_ratings=100,
         positive_review_rate=0.90, has_windows=True, has_mac=True, has_linux=True),
    dict(appid=5, name="AAA Blockbuster", developer="Dev C", publisher="Pub C",
         release_date="2018-11-01", release_year=2018, price=39.99, is_free=False,
         price_tier="AAA ($30+)", positive_ratings=70, negative_ratings=30, total_ratings=100,
         positive_review_rate=0.70, has_windows=True, has_mac=False, has_linux=False),
    # 2019 is the "partial year" (data ends 2019-05-01 in the real dataset) —
    # its YoY must render null regardless of what the raw math would say.
    dict(appid=6, name="Niche Gem", developer="Dev A", publisher="Pub A",
         release_date="2019-04-01", release_year=2019, price=4.99, is_free=False,
         price_tier="Budget ($0.01-$4.99)", positive_ratings=95, negative_ratings=5, total_ratings=100,
         positive_review_rate=0.95, has_windows=True, has_mac=False, has_linux=False),
]

FIXTURE_GENRES = [
    (1, "Indie"), (2, "Indie"), (2, "Action"), (3, "Action"), (3, "RPG"),
    (4, "Action"), (4, "Strategy"), (5, "Action"), (6, "Indie"),
]


@pytest.fixture(scope="session", autouse=True)
def _seeded_database():
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.begin() as conn:
        conn.execute(text(SCHEMA_SQL_PATH.read_text(encoding="utf-8")))
        conn.execute(text("TRUNCATE TABLE game_genres, fact_games RESTART IDENTITY CASCADE"))

        columns = list(FIXTURE_GAMES[0].keys())
        insert_fact = text(
            f"INSERT INTO fact_games ({', '.join(columns)}) VALUES ({', '.join(f':{c}' for c in columns)})"
        )
        for game in FIXTURE_GAMES:
            conn.execute(insert_fact, game)

        insert_genre = text("INSERT INTO game_genres (appid, genre) VALUES (:appid, :genre)")
        for appid, genre in FIXTURE_GENRES:
            conn.execute(insert_genre, {"appid": appid, "genre": genre})
    engine.dispose()
    yield


@pytest.fixture()
def client() -> TestClient:
    from app.main import app  # imported after DATABASE_URL presence is confirmed above

    return TestClient(app)