from __future__ import annotations

from collections import OrderedDict
import time
from typing import Any

from Src.cache.key_builder import CacheKeyBuilder


class RankingCache:
    def __init__(self, max_cache_size_mb: int = 100, ttl_seconds: int = 3600) -> None:
        self.max_cache_size_bytes = max_cache_size_mb * 1024 * 1024
        self.ttl_seconds = ttl_seconds
        self.entries: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self.current_size_bytes = 0
        self.key_builder = CacheKeyBuilder()

    @staticmethod
    def _estimate_size(value: Any) -> int:
        text = repr(value)
        return len(text.encode("utf-8"))

    def _is_expired(self, entry: dict[str, Any]) -> bool:
        return (time.time() - entry["created_at"]) > self.ttl_seconds

    def get(self, key: str) -> dict[str, Any] | None:
        entry = self.entries.get(key)
        if entry is None:
            return None

        if self._is_expired(entry):
            self._remove(key)
            return None

        entry["hits"] += 1
        self.entries.move_to_end(key)
        return entry["value"]

    def set(self, key: str, value: Any, strategy_name: str) -> None:
        if key in self.entries:
            self._remove(key)

        estimated = self._estimate_size(value)
        entry = {
            "key": key,
            "value": value,
            "strategy": strategy_name,
            "created_at": time.time(),
            "hits": 0,
            "size": estimated,
        }

        self.entries[key] = entry
        self.current_size_bytes += estimated
        self.entries.move_to_end(key)
        self._evict_if_needed()

    def _remove(self, key: str) -> None:
        entry = self.entries.pop(key, None)
        if entry:
            self.current_size_bytes -= int(entry["size"])

    def _evict_if_needed(self) -> None:
        while self.current_size_bytes > self.max_cache_size_bytes and self.entries:
            oldest_key, oldest = self.entries.popitem(last=False)
            self.current_size_bytes -= int(oldest["size"])

    def clear_all(self) -> int:
        removed = len(self.entries)
        self.entries.clear()
        self.current_size_bytes = 0
        return removed

    def clear_strategy(self, strategy: str) -> int:
        keys = [
            key for key, entry in self.entries.items() if entry.get("strategy") == strategy
        ]
        for key in keys:
            self._remove(key)
        return len(keys)

    def stats(self) -> dict[str, Any]:
        return {
            "entries": len(self.entries),
            "bytes": self.current_size_bytes,
            "max_bytes": self.max_cache_size_bytes,
            "ttl_seconds": self.ttl_seconds,
        }
