from __future__ import annotations

from fastapi.testclient import TestClient

from Src.api.app import create_app



def test_health_endpoint_smoke() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert "timestamp" in payload



def test_rank_valid_weighted_request_smoke() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/rank",
        json={
            "strategy": "weighted",
            "strategy_params": {"weights": "default"},
            "algorithm": "auto",
            "k": 10,
            "use_cache": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "ranked_products" in body
    assert len(body["ranked_products"]) == 10



def test_rank_invalid_strategy() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/rank",
        json={
            "strategy": "invalid_strategy",
            "strategy_params": {},
        },
    )
    assert response.status_code == 400
    body = response.json()
    assert body["error_code"] == "invalid_strategy"
