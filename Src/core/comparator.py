from __future__ import annotations

from functools import cmp_to_key

from Src.core.strategies import (
    COST_FEATURES,
    LexicographicStrategy,
    SingleAscStrategy,
    SingleDescStrategy,
    WeightedStrategy,
)
from Src.core.types import ProductRecord


class DeterministicComparator:
    def __init__(self, strategy: object, active_features: list[str]) -> None:
        self.strategy = strategy
        self.active_features = active_features

    @staticmethod
    def _cmp_value(a: float, b: float) -> int:
        if a < b:
            return -1
        if a > b:
            return 1
        return 0

    @staticmethod
    def _cmp_text(a: str, b: str) -> int:
        if a < b:
            return -1
        if a > b:
            return 1
        return 0

    def _compare_weighted(self, p1: ProductRecord, p2: ProductRecord) -> int:
        score_1 = round(float(p1.primary_score or 0.0), 12)
        score_2 = round(float(p2.primary_score or 0.0), 12)
        if abs(score_1 - score_2) > 1e-9:
            return -1 if score_1 > score_2 else 1

        tie_chain: list[tuple[str, str]] = [
            ("rating", "desc"),
            ("discount", "desc"),
            ("reviews_count", "desc"),
            ("price", "asc"),
            ("delivery_time", "asc"),
        ]

        for feature, direction in tie_chain:
            if feature in {"discount", "reviews_count", "delivery_time"} and feature not in self.active_features:
                continue

            left = p1.value_for(feature)
            right = p2.value_for(feature)
            cmp = self._cmp_value(left, right)
            if cmp != 0:
                return cmp if direction == "asc" else -cmp

        cmp = self._cmp_text(p1.product_id, p2.product_id)
        if cmp != 0:
            return cmp

        return self._cmp_value(float(p1.row_uid), float(p2.row_uid))

    def compare_fn(self, p1: ProductRecord, p2: ProductRecord) -> int:
        strategy = self.strategy

        if isinstance(strategy, SingleAscStrategy):
            primary = self._cmp_value(
                p1.value_for(strategy.attribute), p2.value_for(strategy.attribute)
            )
            if primary != 0:
                return primary

        elif isinstance(strategy, SingleDescStrategy):
            primary = self._cmp_value(
                p1.value_for(strategy.attribute), p2.value_for(strategy.attribute)
            )
            if primary != 0:
                return -primary

        elif isinstance(strategy, LexicographicStrategy):
            for attribute in strategy.priority:
                primary = self._cmp_value(
                    p1.value_for(attribute), p2.value_for(attribute)
                )
                if primary == 0:
                    continue
                if attribute in COST_FEATURES:
                    return primary
                return -primary

        elif isinstance(strategy, WeightedStrategy):
            return self._compare_weighted(p1, p2)

        cmp = self._cmp_text(p1.product_id, p2.product_id)
        if cmp != 0:
            return cmp

        return self._cmp_value(float(p1.row_uid), float(p2.row_uid))

    def get_sort_key(self):
        return cmp_to_key(self.compare_fn)
