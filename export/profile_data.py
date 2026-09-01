"""
export/profile_data.py

Lightweight, scriptable profile of the Gold-layer export - run this BEFORE
export_to_postgres.py to sanity-check a new extract without touching Postgres.
Not a replacement for notebooks/01_profiling.ipynb (that's the deep EDA);
this is a fast pass/fail gate plus a human-readable report.

Usage:
    python export/profile_data.py [--source auto|databricks|files] [--report path]
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from answer_key import (
    EXPECTED_2018_RELEASES,
    EXPECTED_ACTION_SHARE_PCT,
    EXPECTED_AVG_PAID_PRICE,
    EXPECTED_FREE_SHARE_PCT,
    EXPECTED_INDIE_SHARE_PCT,
    EXPECTED_PRICE_REVIEW_CORRELATION,
    EXPECTED_RPG_COUNT,
    EXPECTED_TOTAL_GAMES,
)
from export_to_postgres import extract  # reuse the same extraction logic

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s %(message)s")
log = logging.getLogger("profile")


def _pct(n: int, d: int) -> float:
    return round(100 * n / d, 2) if d else float("nan")


def build_report(fact: pd.DataFrame, genres: pd.DataFrame) -> tuple[str, bool]:
    lines: list[str] = []
    all_ok = True

    def check(label: str, actual: float, expected: float, tol: float) -> None:
        nonlocal all_ok
        ok = abs(actual - expected) <= tol
        all_ok = all_ok and ok
        status = "OK" if ok else "MISMATCH"
        lines.append(f"[{status:8}] {label}: got {actual}, expected {expected} (+/- {tol})")

    lines.append(f"# Gold export profile - {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## Shape")
    lines.append(f"- fact_games: {len(fact)} rows, {fact.shape[1]} columns")
    lines.append(f"- game_genres: {len(genres)} rows, {genres['genre'].nunique()} distinct genres")
    lines.append("")

    lines.append("## Nulls in fact_games (non-zero columns only)")
    null_counts = fact.isna().sum().sort_values(ascending=False)
    for col, n in null_counts.items():
        if n:
            lines.append(f"- {col}: {n} nulls ({_pct(int(n), len(fact))}%)")
    lines.append("")

    lines.append("## Structural checks")
    dupes = int(fact["appid"].duplicated().sum())
    lines.append(f"- duplicate appid rows: {dupes}")
    all_ok = all_ok and dupes == 0
    orphaned = set(genres["appid"]) - set(fact["appid"])
    lines.append(f"- game_genres rows with no matching fact_games appid: {len(orphaned)}")
    all_ok = all_ok and len(orphaned) == 0
    lines.append("")

    lines.append("## Answer-key checks (tolerant of rounding)")
    check("total games", len(fact), EXPECTED_TOTAL_GAMES, tol=0)

    paid = fact.loc[~fact["is_free"], "price"]
    check("avg paid price (USD)", round(float(paid.mean()), 2), EXPECTED_AVG_PAID_PRICE, tol=0.02)
    check("free games share (%)", _pct(int(fact["is_free"].sum()), len(fact)), EXPECTED_FREE_SHARE_PCT, tol=0.1)

    indie_appids = set(genres.loc[genres["genre"] == "Indie", "appid"])
    action_appids = set(genres.loc[genres["genre"] == "Action", "appid"])
    rpg_count = int((genres["genre"] == "RPG").sum())
    check("Indie share (%)", _pct(len(indie_appids), len(fact)), EXPECTED_INDIE_SHARE_PCT, tol=0.1)
    check("Action share (%)", _pct(len(action_appids), len(fact)), EXPECTED_ACTION_SHARE_PCT, tol=0.1)
    check("RPG count", rpg_count, EXPECTED_RPG_COUNT, tol=0)

    releases_2018 = int((fact["release_year"] == 2018).sum())
    check("2018 releases", releases_2018, EXPECTED_2018_RELEASES, tol=0)

    paid_reviewed = fact.loc[(~fact["is_free"]) & (fact["total_ratings"] > 0)]
    corr = round(float(paid_reviewed["price"].corr(paid_reviewed["positive_review_rate"])), 4)
    check("price vs review-rate correlation", corr, EXPECTED_PRICE_REVIEW_CORRELATION, tol=0.01)

    lines.append("")
    lines.append(f"## Result: {'PASS' if all_ok else 'FAIL - see MISMATCH lines above'}")

    return "\n".join(lines), all_ok


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Profile the Gold export before loading it into Postgres.")
    parser.add_argument("--source", choices=["auto", "databricks", "files"], default="auto")
    parser.add_argument("--report", default="export/profile_report.md",
                         help="Where to write the markdown report (default: export/profile_report.md)")
    args = parser.parse_args()

    result = extract(args.source)
    report, passed = build_report(result.fact_games, result.game_genres)

    print(report)
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(report, encoding="utf-8")
    log.info("Report written to %s", args.report)

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())