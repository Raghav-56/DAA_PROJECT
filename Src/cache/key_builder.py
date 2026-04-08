from __future__ import annotations

import hashlib
import json
from typing import Any


class CacheKeyBuilder:
    @staticmethod
    def _normalize_numbers(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: CacheKeyBuilder._normalize_numbers(value[key])
                for key in sorted(value)
            }
        if isinstance(value, list):
            return [CacheKeyBuilder._normalize_numbers(item) for item in value]
        if isinstance(value, float):
            return float(f"{value:.12g}")
        return value

    def build_key(
        self,
        strategy: str,
        strategy_params: dict[str, Any],
        algorithm: str,
        k: int,
    ) -> str:
        payload = {
            "strategy": strategy,
            "strategy_params": self._normalize_numbers(strategy_params),
            "algorithm": algorithm,
            "k": int(k),
        }
        encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
