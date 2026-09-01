"""
export/validate_load.py

Post-load validation: connects to the Postgres DB that export_to_postgres.py
just populated and re-derives the answer-key metrics with plain SQL (the same
kind of query the FastAPI endpoints will run later). Exits non-zero on any
mismatch.

This is the "did the load actually work" check; profile_data.py is the
"is the source data itself sane" check that runs BEFORE the load.

Usage:
    python export/validate_load.py
"""
from __future__ import annotations

import logging
import sys

from dotenv import load_dotenv
from sqlalchemy import text

from answer_key import (
    EXPECTED_2018_RELEASES,
    EXPECTED_ACTION_SHARE_PCT,
    EXPECTED_AVG_PAID_PRICE,
    EXPECTED_FREE_SHARE_PCT,
    EXPECTED_INDIE_SHARE_PCT,
    EXPECTED_PRICE_REVIEW_CORRELATION,
    EXPECTED_RPG_COUNT,
    EXPECTED_TOTAL_GAMES,
    EXPECTED_YOY_2017_PCT,
    EXPECTED_YOY_2018_PCT,
)
from export_to_postgres import get_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s %(message)s")
log = logging.getLogger("validate")

# (label, sql, expected, tolerance)
CHECKS = [
    ("total games", "SELECT COUNT(*) FROM fact_games", EXPECTED_TOTAL_GAMES, 0),
    (
        "avg paid price (USD)",
        "SELECT ROUND(AVG(price), 2) FROM fact_games WHERE NOT is_free",
        EXPECTED_AVG_PAID_PRICE,
        0.02,
    ),
    (
        "free games share (%)",
        "SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE is_free) / COUNT(*), 2) FROM fact_games",
        EXPECTED_FREE_SHARE_PCT,
        0.1,
    ),
    (
        "Indie share (%)",
        """
        SELECT ROUND(100.0 * COUNT(DISTINCT g.appid) / (SELECT COUNT(*) FROM fact_games), 2)
        FROM game_genres g WHERE g.genre = 'Indie'
        """,
        EXPECTED_INDIE_SHARE_PCT,
        0.1,
    ),
    (
        "Action share (%)",
        """
        SELECT ROUND(100.0 * COUNT(DISTINCT g.appid) / (SELECT COUNT(*) FROM fact_games), 2)
        FROM game_genres g WHERE g.genre = 'Action'
        """,
        EXPECTED_ACTION_SHARE_PCT,
        0.1,
    ),
    ("RPG count", "SELECT COUNT(*) FROM game_genres WHERE genre = 'RPG'", EXPECTED_RPG_COUNT, 0),
    (
        "2018 releases",
        "SELECT COUNT(*) FROM fact_games WHERE release_year = 2018",
        EXPECTED_2018_RELEASES,
        0,
    ),
    (
        "price vs review-rate correlation",
        """
        SELECT ROUND(CORR(price, positive_review_rate)::numeric, 4)
        FROM fact_games WHERE NOT is_free AND total_ratings > 0
        """,
        EXPECTED_PRICE_REVIEW_CORRELATION,
        0.01,
    ),
]

# 2019 is deliberately excluded: it's a partial year (data ends 2019-05-01)
# and YoY must be null for it, never computed.
YOY_SQL = """
WITH by_year AS (
    SELECT release_year, COUNT(*) AS releases
    FROM fact_games
    WHERE release_year BETWEEN 2016 AND 2018
    GROUP BY release_year
)
SELECT release_year,
       ROUND(100.0 * (releases - LAG(releases) OVER (ORDER BY release_year))
             / LAG(releases) OVER (ORDER BY release_year), 1) AS yoy_pct
FROM by_year
ORDER BY release_year
"""


def main() -> int:
    load_dotenv()
    engine = get_engine()
    all_ok = True

    with engine.connect() as conn:
        for label, sql, expected, tol in CHECKS:
            raw = conn.execute(text(sql)).scalar_one()
            actual = float(raw) if raw is not None else float("nan")
            ok = abs(actual - expected) <= tol
            all_ok = all_ok and ok
            log.info("[%s] %s: got %s, expected %s (+/- %s)",
                      "OK" if ok else "MISMATCH", label, actual, expected, tol)

        yoy_rows = {row.release_year: row.yoy_pct for row in conn.execute(text(YOY_SQL))}
        for year, expected_yoy in ((2018, EXPECTED_YOY_2018_PCT), (2017, EXPECTED_YOY_2017_PCT)):
            raw_yoy = yoy_rows.get(year)
            actual_yoy = float(raw_yoy) if raw_yoy is not None else float("nan")
            ok = abs(actual_yoy - expected_yoy) <= 0.2
            all_ok = all_ok and ok
            log.info("[%s] YoY %d: got %s%%, expected %s%%",
                      "OK" if ok else "MISMATCH", year, actual_yoy, expected_yoy)

    if all_ok:
        log.info("All answer-key checks passed.")
    else:
        log.error("One or more answer-key checks FAILED - see MISMATCH lines above.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())