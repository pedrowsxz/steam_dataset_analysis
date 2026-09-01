import pytest


def test_2019_yoy_is_always_null(client):
    resp = client.get("/api/trends/releases")
    assert resp.status_code == 200
    years = {y["year"]: y for y in resp.json()["years"]}
    assert years[2019]["yoy_pct"] is None
    assert resp.json()["notes"]["partial_year"] == 2019


def test_yoy_values_for_complete_years(client):
    resp = client.get("/api/trends/releases")
    years = {y["year"]: y for y in resp.json()["years"]}
    # 2016: 1 release, 2017: 2 releases -> +100%; 2018: 2 releases -> +0%
    assert years[2017]["yoy_pct"] == pytest.approx(100.0, abs=0.1)
    assert years[2018]["yoy_pct"] == pytest.approx(0.0, abs=0.1)
    assert years[2016]["yoy_pct"] is None  # no prior year in the trimmed series


def test_platforms_shape(client):
    resp = client.get("/api/trends/platforms")
    assert resp.status_code == 200
    years = {y["year"]: y for y in resp.json()["years"]}
    # 2018: appid 4 has mac+linux, appid 5 has neither -> 50%/50%
    assert years[2018]["pct_mac"] == pytest.approx(50.0, abs=0.1)
    assert years[2018]["pct_linux"] == pytest.approx(50.0, abs=0.1)
    assert years[2018]["pct_windows"] == pytest.approx(100.0, abs=0.1)


def test_publishers_ranked_desc_by_count(client):
    resp = client.get("/api/trends/publishers?limit=3")
    assert resp.status_code == 200
    publishers = resp.json()["publishers"]
    assert publishers[0]["publisher"] == "Pub A"
    assert publishers[0]["game_count"] == 3
    counts = [p["game_count"] for p in publishers]
    assert counts == sorted(counts, reverse=True)


def test_publishers_note_warns_against_market_share_framing(client):
    resp = client.get("/api/trends/publishers")
    assert "market share" in resp.json()["note"]