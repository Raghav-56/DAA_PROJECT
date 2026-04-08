from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from Src.api.app import create_app


@pytest.mark.smoke
def test_cache_hit_miss_and_clear() -> None:
    client = TestClient(create_app())
    payload = {
        "strategy": "weighted",
        "strategy_params": {"weights": "default"},
        "algorithm": "auto",
        "k": 20,
        "use_cache": True,
    }

    first = client.post("/rank", json=payload)
    second = client.post("/rank", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["execution_metrics"]["cache_hit"] is False
    assert second.json()["execution_metrics"]["cache_hit"] is True

    cleared = client.post("/cache/clear")
    assert cleared.status_code == 200
    assert cleared.json()["status"] == "success"
