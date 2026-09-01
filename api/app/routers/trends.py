"""api/app/routers/trends.py — Temporal Trends tab."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import (
    PlatformYear,
    PlatformsResponse,
    PublisherRow,
    PublishersResponse,
    ReleaseNotes,
    ReleasesResponse,
    YearRelease,
)

router = APIRouter(prefix="/api/trends", tags=["trends"])

MIN_TREND_YEAR = 2006  # years before this have <50 releases and are documented as noisy
PARTIAL_YEAR = 2019    # data ends 2019-05-01; YoY forced null for this year, no exceptions


@router.get("/releases", response_model=ReleasesResponse)
def releases(db: Session = Depends(get_db)) -> ReleasesResponse:
    rows = db.execute(
        text(
            """
            SELECT release_year AS year, COUNT(*) AS releases
            FROM fact_games
            WHERE release_year >= :min_year
            GROUP BY release_year
            ORDER BY release_year
            """
        ),
        {"min_year": MIN_TREND_YEAR},
    ).all()

    years: list[YearRelease] = []
    prev_releases: int | None = None
    for r in rows:
        if r.year == PARTIAL_YEAR:
            yoy = None  # never computed for a partial year, regardless of what the raw math would say
        elif prev_releases:
            yoy = round(100 * (r.releases - prev_releases) / prev_releases, 1)
        else:
            yoy = None  # first year in the trimmed series has no prior year to compare against
        years.append(YearRelease(year=r.year, releases=r.releases, yoy_pct=yoy))
        prev_releases = r.releases

    return ReleasesResponse(
        years=years,
        notes=ReleaseNotes(
            trimmed_years_before=MIN_TREND_YEAR,
            partial_year=PARTIAL_YEAR,
            partial_year_reason="Data ends 2019-05-01.",
        ),
    )


@router.get("/platforms", response_model=PlatformsResponse)
def platforms(db: Session = Depends(get_db)) -> PlatformsResponse:
    rows = db.execute(
        text(
            """
            SELECT
                release_year AS year,
                ROUND(100.0 * COUNT(*) FILTER (WHERE has_windows) / COUNT(*), 1) AS pct_windows,
                ROUND(100.0 * COUNT(*) FILTER (WHERE has_mac) / COUNT(*), 1) AS pct_mac,
                ROUND(100.0 * COUNT(*) FILTER (WHERE has_linux) / COUNT(*), 1) AS pct_linux
            FROM fact_games
            WHERE release_year >= :min_year
            GROUP BY release_year
            ORDER BY release_year
            """
        ),
        {"min_year": MIN_TREND_YEAR},
    ).all()
    return PlatformsResponse(
        years=[
            PlatformYear(
                year=r.year, pct_windows=float(r.pct_windows),
                pct_mac=float(r.pct_mac), pct_linux=float(r.pct_linux),
            )
            for r in rows
        ],
        note="Only 5 games in the whole dataset lack Windows — the story here is Mac/Linux, not Windows.",
    )


@router.get("/publishers", response_model=PublishersResponse)
def publishers(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> PublishersResponse:
    rows = db.execute(
        text(
            """
            SELECT
                publisher,
                COUNT(*) AS game_count,
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM fact_games), 2) AS pct_of_games
            FROM fact_games
            WHERE publisher IS NOT NULL
            GROUP BY publisher
            ORDER BY game_count DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).all()
    return PublishersResponse(
        publishers=[
            PublisherRow(publisher=r.publisher, game_count=r.game_count, pct_of_games=float(r.pct_of_games))
            for r in rows
        ],
        note="Ranked by game count. Publishers are a fragmented long tail — never describe this as market share.",
    )