"""api/app/routers/pricing.py — Pricing & Reviews tab."""
import random

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import (
    FreeVsPaidBucket,
    FreeVsPaidResponse,
    PriceTierRow,
    PriceTiersResponse,
    ScatterCorrelation,
    ScatterPoint,
    ScatterResponse,
    ScatterSampling,
)

router = APIRouter(prefix="/api/pricing", tags=["pricing"])

# Fixed display order — never sort this alphabetically or by count; the
# chart reads left-to-right as "cheapest to most expensive".
TIER_ORDER = [
    "Free",
    "Budget ($0.01-$4.99)",
    "Standard ($5-$14.99)",
    "Premium ($15-$29.99)",
    "AAA ($30+)",
]

SCATTER_SEED = 42
SCATTER_DEFAULT_LIMIT = 1500
SCATTER_MAX_LIMIT = 3000


@router.get("/tiers", response_model=PriceTiersResponse)
def tiers(db: Session = Depends(get_db)) -> PriceTiersResponse:
    rows = db.execute(
        text(
            """
            SELECT
                price_tier AS tier,
                COUNT(*) AS game_count,
                ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM fact_games), 2) AS pct_of_games
            FROM fact_games
            GROUP BY price_tier
            """
        )
    ).all()
    by_tier = {r.tier: r for r in rows}
    ordered = [
        PriceTierRow(tier=t, game_count=by_tier[t].game_count, pct_of_games=float(by_tier[t].pct_of_games))
        for t in TIER_ORDER
        if t in by_tier
    ]
    return PriceTiersResponse(tiers=ordered)


@router.get("/free-vs-paid", response_model=FreeVsPaidResponse)
def free_vs_paid(db: Session = Depends(get_db)) -> FreeVsPaidResponse:
    """The one place a donut chart is appropriate — is_free is genuinely
    binary, unlike genres."""
    row = db.execute(
        text(
            """
            SELECT
                COUNT(*) FILTER (WHERE is_free) AS free_count,
                COUNT(*) FILTER (WHERE NOT is_free) AS paid_count,
                COUNT(*) AS total
            FROM fact_games
            """
        )
    ).one()
    return FreeVsPaidResponse(
        free=FreeVsPaidBucket(game_count=row.free_count, pct=round(100 * row.free_count / row.total, 2)),
        paid=FreeVsPaidBucket(game_count=row.paid_count, pct=round(100 * row.paid_count / row.total, 2)),
    )


@router.get("/scatter", response_model=ScatterResponse)
def scatter(
    limit: int = Query(default=SCATTER_DEFAULT_LIMIT, ge=1, le=SCATTER_MAX_LIMIT),
    db: Session = Depends(get_db),
) -> ScatterResponse:
    """Never ships all ~27k rows to the browser. Sampling is stratified by
    price_tier (not pure random) so cheap and expensive games stay
    proportionally represented regardless of row order. The correlation is
    computed server-side over the FULL eligible population, not the sample,
    so it stays accurate no matter what `limit` the client asks for."""
    corr_row = db.execute(
        text(
            """
            SELECT ROUND(CORR(price, positive_review_rate)::numeric, 4) AS r
            FROM fact_games
            WHERE NOT is_free AND total_ratings > 0
            """
        )
    ).one()

    eligible = db.execute(
        text(
            """
            SELECT appid, name, price, positive_review_rate, price_tier
            FROM fact_games
            WHERE NOT is_free AND total_ratings > 0
            """
        )
    ).all()

    rng = random.Random(SCATTER_SEED)
    by_tier: dict[str, list] = {}
    for row in eligible:
        by_tier.setdefault(row.price_tier, []).append(row)

    sample_size = min(limit, len(eligible))
    sampled: list = []
    selected_appids: set[int] = set()

    if eligible:
        # Proportional allocation per tier; rounding means the total can land
        # slightly above or below sample_size, corrected by the trim/top-up below.
        for tier_rows in by_tier.values():
            tier_quota = round(sample_size * len(tier_rows) / len(eligible))
            picked = rng.sample(tier_rows, k=min(tier_quota, len(tier_rows)))
            sampled.extend(picked)
            selected_appids.update(r.appid for r in picked)

        if len(sampled) > sample_size:
            sampled = rng.sample(sampled, k=sample_size)
        elif len(sampled) < sample_size:
            remaining = [r for r in eligible if r.appid not in selected_appids]
            sampled.extend(rng.sample(remaining, k=min(sample_size - len(sampled), len(remaining))))

    return ScatterResponse(
        points=[
            ScatterPoint(
                appid=r.appid, name=r.name, price=float(r.price),
                positive_review_rate=r.positive_review_rate, price_tier=r.price_tier,
            )
            for r in sampled
        ],
        sampling=ScatterSampling(
            method="stratified_random_by_price_tier",
            seed=SCATTER_SEED,
            eligible_rows=len(eligible),
            sample_size=len(sampled),
        ),
        correlation=ScatterCorrelation(
            pearson_r=float(corr_row.r) if corr_row.r is not None else None,
            note="Effectively uncorrelated — do not present this chart as showing a relationship.",
        ),
    )