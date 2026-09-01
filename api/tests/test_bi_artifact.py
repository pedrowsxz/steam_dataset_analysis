def test_bi_artifact_metadata(client):
    resp = client.get("/api/bi-artifact/metadata")
    assert resp.status_code == 200
    body = resp.json()
    assert body["pbix_reference"]["filename"] == "steam_dashboard.pbix"
    assert isinstance(body["dax_measures"], list) and len(body["dax_measures"]) > 0
    assert body["powerbi_embed_url"] is None  # unset in this test environment