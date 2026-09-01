import pandas as pd
import pytest


def test_tiers_in_fixed_display_order(client):
    resp = client.get("/api/pricing/tiers")
    assert resp.status_code == 200
    tiers = [t["tier"] for t in resp.json()["tiers"]]
    assert tiers == [
        "Free",
        "Budget ($0.01-$4.99)",
        "Standard ($5-$14.99)",
        "Premium ($15-$29.99)",
        "AAA ($30+)",
    ]


def test_tiers_counts(client):
    resp = client.get("/api/pricing/tiers")
    by_tier = {t["tier"]: t["game_count"] for t in resp.json()["tiers"]}
    assert by_tier["Budget ($0.01-$4.99)"] == 2  # appid 2 and 6
    assert by_tier["Free"] == 1


def test_free_vs_paid(client):
    resp = client.get("/api/pricing/free-vs-paid")
    assert resp.status_code == 200
    body = resp.json()
    assert body["free"]["game_count"] == 1
    assert body["paid"]["game_count"] == 5
    assert body["free"]["pct"] + body["paid"]["pct"] == pytest.approx(100.0, abs=0.01)


def test_scatter_respects_limit(client):
    resp = client.get("/api/pricing/scatter?limit=2")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["points"]) <= 2
    assert body["sampling"]["sample_size"] == len(body["points"])
    assert body["sampling"]["eligible_rows"] == 5  # 6 games minus 1 free game


def test_scatter_rejects_out_of_range_limit(client):
    assert client.get("/api/pricing/scatter?limit=0").status_code == 422
    assert client.get("/api/pricing/scatter?limit=999999").status_code == 422


def test_scatter_correlation_matches_full_population(client):
    """Ask for every eligible row and confirm the server-reported correlation
    matches a from-scratch calculation over exactly those points."""
    resp = client.get("/api/pricing/scatter?limit=100")
    body = resp.json()
    df = pd.DataFrame(body["points"])
    expected_r = df["price"].corr(df["positive_review_rate"])
    assert body["correlation"]["pearson_r"] == pytest.approx(expected_r, abs=0.001)
    assert "do not present" in body["correlation"]["note"]