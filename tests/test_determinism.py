from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from Src.api.app import create_app


@pytest.mark.smoke
def test_repeated_requests_are_deterministic() -> None:
    client = TestClient(create_app())
    request_body = {
        "strategy": "single_desc",
        "strategy_params": {"attribute": "rating"},
        "algorithm": "quick_sort",
        "k": 50,
        "use_cache": False,
    }

    first = client.post("/rank", json=request_body)
    second = client.post("/rank", json=request_body)

    assert first.status_code == 200
    assert second.status_code == 200

    ids_1 = [item["product_id"] for item in first.json()["ranked_products"]]
    ids_2 = [item["product_id"] for item in second.json()["ranked_products"]]
    assert ids_1 == ids_2
