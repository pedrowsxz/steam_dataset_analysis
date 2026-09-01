import pytest


def test_summary(client):
    resp = client.get("/api/overview/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_games"] == 6
    assert body["avg_paid_price_usd"] == pytest.approx(15.79, abs=0.01)
    assert body["free_games_pct"] == pytest.approx(16.67, abs=0.01)


def test_genres_sorted_desc_and_respects_limit(client):
    resp = client.get("/api/overview/genres?limit=2")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["genres"]) == 2
    counts = [g["game_count"] for g in body["genres"]]
    assert counts == sorted(counts, reverse=True)
    # Action appears on appids 2,3,4,5 -> 4 of 6 games
    assert body["genres"][0]["genre"] == "Action"
    assert body["genres"][0]["game_count"] == 4
    assert body["genres"][0]["pct_of_games"] == pytest.approx(66.67, abs=0.01)


def test_genres_percentages_dont_have_to_sum_to_100(client):
    resp = client.get("/api/overview/genres?limit=50")
    body = resp.json()
    total_pct = sum(g["pct_of_games"] for g in body["genres"])
    assert total_pct > 100  # multi-label overlap, exactly as documented
    assert "do not sum to 100%" in body["note"]


def test_genres_limit_is_bounded(client):
    resp = client.get("/api/overview/genres?limit=0")
    assert resp.status_code == 422
    resp = client.get("/api/overview/genres?limit=51")
    assert resp.status_code == 422