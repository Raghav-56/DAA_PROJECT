from __future__ import annotations

from dataclasses import replace
import time
from typing import Any

from Src.core.algorithms import HeapTopKRanker, MergeSortRanker, QuickSortRanker
from Src.core.auto_select import select_algorithm
from Src.core.comparator import DeterministicComparator
from Src.core.strategies import RankingStrategy, WeightedStrategy
from Src.core.types import PreprocessedDataset, RankingResult


class RankingEngine:
    def __init__(
        self,
        dataset: PreprocessedDataset,
        strategy: RankingStrategy,
        comparator: DeterministicComparator,
        cache: Any | None = None,
    ) -> None:
        self.dataset = dataset
        self.strategy = strategy
        self.comparator = comparator
        self.cache = cache

    def rank(
        self,
        k: int = 100,
        algorithm: str = "auto",
        use_cache: bool = True,
        strategy_name: str | None = None,
        strategy_params: dict[str, Any] | None = None,
        quick_sort_fraction_threshold: float = 0.30,
        heap_preferred_k_threshold: int = 1000,
    ) -> RankingResult:
        products = [replace(product) for product in self.dataset.products]
        n = len(products)
        effective_k = min(k, n)

        cache_key: str | None = None
        if (
            use_cache
            and self.cache is not None
            and strategy_name is not None
            and strategy_params is not None
        ):
            cache_key = self.cache.key_builder.build_key(
                strategy_name,
                strategy_params,
                algorithm,
                effective_k,
            )
            cached = self.cache.get(cache_key)
            if cached is not None:
                return RankingResult(
                    ranked_products=cached["ranked_products"],
                    algorithm_used=cached["algorithm_used"],
                    algorithm_time_ms=cached["algorithm_time_ms"],
                    cache_hit=True,
                    cache_key=cache_key,
                    fallback_applied=cached.get("fallback_applied", False),
                    active_weights=cached.get("active_weights"),
                )

        self.strategy.prepare_products(products)

        algorithm_used = select_algorithm(
            algorithm,
            effective_k,
            n,
            quick_sort_fraction_threshold=quick_sort_fraction_threshold,
            heap_preferred_k_threshold=heap_preferred_k_threshold,
        )

        rankers = {
            "merge_sort": MergeSortRanker(),
            "quick_sort": QuickSortRanker(),
            "heap_top_k": HeapTopKRanker(),
        }
        ranker = rankers[algorithm_used]

        start = time.perf_counter()
        ranked = ranker.rank(products, self.comparator, effective_k)
        elapsed_ms = round((time.perf_counter() - start) * 1000.0, 3)

        active_weights = (
            self.strategy.active_weights()
            if isinstance(self.strategy, WeightedStrategy)
            else None
        )

        result = RankingResult(
            ranked_products=ranked,
            algorithm_used=algorithm_used,
            algorithm_time_ms=elapsed_ms,
            cache_hit=False,
            cache_key=cache_key,
            active_weights=active_weights,
        )

        if cache_key and self.cache is not None and use_cache:
            self.cache.set(
                cache_key,
                {
                    "ranked_products": ranked,
                    "algorithm_used": algorithm_used,
                    "algorithm_time_ms": elapsed_ms,
                    "fallback_applied": result.fallback_applied,
                    "active_weights": active_weights,
                },
                strategy_name=strategy_name,
            )

        return result
