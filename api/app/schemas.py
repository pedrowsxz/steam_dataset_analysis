"""
api/app/schemas.py

Response models for every endpoint. These exist for three reasons: FastAPI
validates outgoing data against them (a bug that produces the wrong shape
fails loudly instead of shipping silently), they generate accurate OpenAPI
docs at /docs, and the frontend can codegen types from them later if useful.
"""
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: str
    db_latency_ms: float | None = None


# --- Market Overview ---------------------------------------------------

class OverviewSummary(BaseModel):
    total_games: int
    avg_paid_price_usd: float
    free_games_pct: float


class GenreRow(BaseModel):
    genre: str
    game_count: int
    pct_of_games: float


class GenresResponse(BaseModel):
    genres: list[GenreRow]
    note: str


# --- Pricing & Reviews ---------------------------------------------------

class PriceTierRow(BaseModel):
    tier: str
    game_count: int
    pct_of_games: float


class PriceTiersResponse(BaseModel):
    tiers: list[PriceTierRow]


class FreeVsPaidBucket(BaseModel):
    game_count: int
    pct: float


class FreeVsPaidResponse(BaseModel):
    free: FreeVsPaidBucket
    paid: FreeVsPaidBucket


class ScatterPoint(BaseModel):
    appid: int
    name: str
    price: float
    positive_review_rate: float | None
    price_tier: str


class ScatterSampling(BaseModel):
    method: str
    seed: int
    eligible_rows: int
    sample_size: int


class ScatterCorrelation(BaseModel):
    pearson_r: float | None
    note: str


class ScatterResponse(BaseModel):
    points: list[ScatterPoint]
    sampling: ScatterSampling
    correlation: ScatterCorrelation


# --- Temporal Trends ---------------------------------------------------

class YearRelease(BaseModel):
    year: int
    releases: int
    yoy_pct: float | None


class ReleaseNotes(BaseModel):
    trimmed_years_before: int
    partial_year: int
    partial_year_reason: str


class ReleasesResponse(BaseModel):
    years: list[YearRelease]
    notes: ReleaseNotes


class PlatformYear(BaseModel):
    year: int
    pct_windows: float
    pct_mac: float
    pct_linux: float


class PlatformsResponse(BaseModel):
    years: list[PlatformYear]
    note: str


class PublisherRow(BaseModel):
    publisher: str
    game_count: int
    pct_of_games: float


class PublishersResponse(BaseModel):
    publishers: list[PublisherRow]
    note: str


# --- BI Artifact ---------------------------------------------------

class DaxMeasure(BaseModel):
    name: str
    expression: str
    description: str


class PbixReference(BaseModel):
    filename: str
    note: str


class BiArtifactResponse(BaseModel):
    dax_measures: list[DaxMeasure]
    data_model_notes: str
    pbix_reference: PbixReference
    screenshots: list[str]
    powerbi_embed_url: str | None