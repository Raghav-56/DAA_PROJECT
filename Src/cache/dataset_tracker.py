from __future__ import annotations

from pathlib import Path

from Src.core.dataset import DatasetLoader


class DatasetTracker:
    def __init__(self, dataset_path: str | Path) -> None:
        self.dataset_path = Path(dataset_path)
        self._last_hash: str | None = None

    def current_hash(self) -> str:
        return DatasetLoader(self.dataset_path).compute_hash()

    def has_changed(self) -> bool:
        current = self.current_hash()
        if self._last_hash is None:
            self._last_hash = current
            return False
        changed = current != self._last_hash
        self._last_hash = current
        return changed

    def reset(self) -> None:
        self._last_hash = self.current_hash()
