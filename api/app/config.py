"""
api/app/config.py

Settings are read from process env vars, with a local `.env` (in the api/
directory - see .env.example) as a convenience for `uvicorn app.main:app`
run locally. Render injects real env vars directly in production; no .env
file exists there.
"""
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    frontend_origin: str = "http://localhost:5173"
    # Optional Power BI Service embed URL for the BI Artifact tab. The tab
    # works fully without this - the iframe is additive, never required.
    powerbi_embed_url: str | None = None

    @field_validator("powerbi_embed_url")
    @classmethod
    def _blank_string_means_unset(cls, v: str | None) -> str | None:
        # A .env file with "POWERBI_EMBED_URL=" (present but blank) should
        # behave identically to the var being absent entirely, which is how
        # it will actually appear on Render if never configured.
        return v if v else None


@lru_cache
def get_settings() -> Settings:
    return Settings()