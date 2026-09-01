"""
api/app/routers/bi_artifact.py — BI Artifact tab.

Doesn't depend on Power BI Service being reachable. dax_measures,
data_model_notes, and screenshots are curated ONCE from
powerbi/dax_measures.md into bi_artifact_data.json — no markdown parsing at
request time. powerbi_embed_url is the one field read live from settings,
since it's the one field controlled by an env var per the spec (present the
iframe only if POWERBI_EMBED_URL is set).
"""
import json
from pathlib import Path

from fastapi import APIRouter

from ..config import get_settings
from ..schemas import BiArtifactResponse

router = APIRouter(prefix="/api/bi-artifact", tags=["bi-artifact"])

_DATA_PATH = Path(__file__).resolve().parent.parent / "bi_artifact_data.json"
_CURATED = json.loads(_DATA_PATH.read_text(encoding="utf-8"))


@router.get("/metadata", response_model=BiArtifactResponse)
def metadata() -> BiArtifactResponse:
    data = dict(_CURATED)
    data["powerbi_embed_url"] = get_settings().powerbi_embed_url
    return BiArtifactResponse(**data)