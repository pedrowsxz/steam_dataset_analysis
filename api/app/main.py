"""
api/app/main.py

Run locally:
    cd api && uvicorn app.main:app --reload

Render's start command is the same, just without --reload.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import bi_artifact, health, overview, pricing, trends

settings = get_settings()

app = FastAPI(
    title="Steam Gold Dashboard API",
    description="Server-side aggregates for the Steam BI Lakehouse dashboard. Read-only.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(overview.router)
app.include_router(pricing.router)
app.include_router(trends.router)
app.include_router(bi_artifact.router)