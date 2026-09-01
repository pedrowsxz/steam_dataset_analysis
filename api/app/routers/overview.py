"""api/app/routers/overview.py — Market Overview tab."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import GenreRow, GenresResponse, OverviewSummary

router = APIRouter(prefix="/api/overview", tags=["overview"])


@router.get("/summary", response_model=OverviewSummary)
def summary(db: Session = Depends(get_db)) -> OverviewSummary:
    row = db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_games,
                ROUND(AVG(price) FILTER (WHERE NOT is_free), 2) AS avg_paid_price_usd,
                ROUND(100.0 * COUNT(*) FILTER (WHERE is_free) / COUNT(*), 2) AS free_games_pct
            FROM fact_games
            """
        )
    ).one()
    return OverviewSummary(
        total_games=row.total_games,
        avg_paid_price_usd=float(row.avg_paid_price_usd),
        free_games_pct=float(row.free_games_pct),
    )


@router.get("/genres", response_model=GenresResponse)
def genres(
    limit: int = Query(default=15, ge=1, le=50),
    db: Session = Depends(get_db),
) -> GenresResponse:
    """Top N genres by game count, descending. Percentages are of ALL games
    (denominator = fact_games row count), not of genre-tag occurrences —
    since 85% of games carry more than one genre, these percentages
    deliberately don't sum to 100%."""
    rows = db.execute(
        text(
            """
            SELECT
                g.genre,
                COUNT(*) AS game_count,
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM fact_games), 2) AS pct_of_games
            FROM game_genres g
            GROUP BY g.genre
            ORDER BY game_count DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).all()
    return GenresResponse(
        genres=[GenreRow(genre=r.genre, game_count=r.game_count, pct_of_games=float(r.pct_of_games)) for r in rows],
        note="Games can carry multiple genres; percentages do not sum to 100%.",
    )