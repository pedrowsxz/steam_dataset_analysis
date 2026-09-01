"""
api/app/routers/health.py

Always returns 200 so Render's own health check doesn't restart the dyno
mid cold-start. The `database` field is what the frontend actually watches
to decide whether to show a "waking up, hang tight" state instead of a
blank screen while Neon's compute spins back up.
"""
import time

from fastapi import APIRouter
from sqlalchemy import text

from ..db import engine
from ..schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    start = time.perf_counter()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        return HealthResponse(status="ok", database="ok", db_latency_ms=latency_ms)
    except Exception:
        return HealthResponse(status="ok", database="unreachable", db_latency_ms=None)