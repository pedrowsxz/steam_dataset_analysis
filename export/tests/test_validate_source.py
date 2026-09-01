"""
export/tests/test_validate_source.py

Pure unit tests for the pre-load structural checks in export_to_postgres.py.
No database, no credentials, no network - these run anywhere, including CI,
once we wire a test job up to them.

Usage:
    pytest export/tests/
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # make export/ importable

from export_to_postgres import ExtractResult, REQUIRED_FACT_COLUMNS, validate_source  # noqa: E402


def _minimal_fact(**overrides) -> pd.DataFrame:
    row = {col: None for col in REQUIRED_FACT_COLUMNS}
    row.update(
        appid=1, name="Test Game", price=9.99, is_free=False, price_tier="Standard ($5-$14.99)",
        positive_ratings=10, negative_ratings=2, total_ratings=12, positive_review_rate=0.83,
        achievements=0, owners_min=0, owners_max=20000, owners_avg=10000,
        english=True, required_age=0, has_windows=True, has_mac=False, has_linux=False,
        release_year=2018,
    )
    row.update(overrides)
    return pd.DataFrame([row])


def _minimal_genres(appid=1, genre="Indie") -> pd.DataFrame:
    return pd.DataFrame([{"appid": appid, "genre": genre}])


def test_valid_source_passes(monkeypatch):
    # The fixture is a single synthetic row; patch the expected-row-count
    # threshold down so this test exercises everything EXCEPT that check
    # (which gets its own dedicated test below).
    import export_to_postgres as mod
    monkeypatch.setattr(mod, "EXPECTED_TOTAL_GAMES", 1)
    result = ExtractResult(_minimal_fact(), _minimal_genres(), source="csv_fallback")
    validate_source(result)  # should not raise


def test_missing_column_rejected():
    fact = _minimal_fact().drop(columns=["price"])
    result = ExtractResult(fact, _minimal_genres(), source="csv_fallback")
    with pytest.raises(ValueError, match="missing columns"):
        validate_source(result)


def test_duplicate_appid_rejected():
    fact = pd.concat([_minimal_fact(), _minimal_fact()], ignore_index=True)
    result = ExtractResult(fact, _minimal_genres(), source="csv_fallback")
    with pytest.raises(ValueError, match="duplicate appid"):
        validate_source(result)


def test_null_appid_rejected():
    fact = _minimal_fact(appid=None)
    result = ExtractResult(fact, _minimal_genres(), source="csv_fallback")
    with pytest.raises(ValueError, match="NULL appid"):
        validate_source(result)


def test_orphaned_genre_rejected():
    result = ExtractResult(_minimal_fact(), _minimal_genres(appid=999), source="csv_fallback")
    with pytest.raises(ValueError, match="not in fact_games"):
        validate_source(result)


def test_suspiciously_small_dataset_rejected(monkeypatch):
    import export_to_postgres as mod
    monkeypatch.setattr(mod, "EXPECTED_TOTAL_GAMES", 100)
    result = ExtractResult(_minimal_fact(), _minimal_genres(), source="csv_fallback")
    with pytest.raises(ValueError, match="suspiciously small"):
        validate_source(result)