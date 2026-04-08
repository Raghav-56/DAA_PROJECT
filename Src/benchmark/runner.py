from __future__ import annotations

from dataclasses import replace
import statistics
import time
from pathlib import Path

from Src.common.utils import get_iso8601_timestamp
from Src.core.comparator import DeterministicComparator
from Src.core.engine import RankingEngine
from Src.core.pipeline import preprocess_dataset
from Src.core.strategies import build_strategy
from Src.core.types import BenchmarkResult, BenchmarkRun, PreprocessedDataset


class BenchmarkRunner:
    def __init__(self, dataset_path: str | Path) -> None:
        self.dataset_path = Path(dataset_path)
        self.dataset = preprocess_dataset(self.dataset_path)

    @staticmethod
    def _subset_dataset(
        dataset: PreprocessedDataset, dataset_size: int
    ) -> PreprocessedDataset:
        size = min(dataset_size, len(dataset.products))
        subset_products = [replace(product) for product in dataset.products[:size]]
        return PreprocessedDataset(
            products=subset_products,
            active_features=list(dataset.active_features),
            feature_reasons=dict(dataset.feature_reasons),
            normalization_stats=dict(dataset.normalization_stats),
            dropped_rows=dataset.dropped_rows,
            source_path=dataset.source_path,
            dataset_hash=dataset.dataset_hash,
        )

    def run_matrix(
        self, runs: list[BenchmarkRun]
    ) -> tuple[list[BenchmarkResult], list[dict], dict]:
        results: list[BenchmarkResult] = []
        outputs: list[dict] = []

        for run in runs:
            subset = self._subset_dataset(self.dataset, run.dataset_size)
            strategy, fallback_applied = build_strategy(
                run.strategy,
                run.strategy_params,
                subset.active_features,
                allow_fallback=False,
            )
            comparator = DeterministicComparator(strategy, subset.active_features)

            ranking_times: list[float] = []
            end_to_end_times: list[float] = []
            top_ids: list[str] = []

            for iteration in range(7):
                engine = RankingEngine(subset, strategy, comparator, cache=None)
                started = time.perf_counter()
                ranking_result = engine.rank(
                    k=run.k,
                    algorithm=run.algorithm,
                    use_cache=False,
                )
                total_ms = (time.perf_counter() - started) * 1000.0

                if iteration >= 2:
                    ranking_times.append(ranking_result.algorithm_time_ms)
                    end_to_end_times.append(round(total_ms, 3))

                if not top_ids:
                    top_ids = [item.product_id for item in ranking_result.ranked_products]

            timestamp = get_iso8601_timestamp()
            results.append(
                BenchmarkResult(
                    algorithm=run.algorithm,
                    ranking_strategy=run.strategy,
                    dataset_size=run.dataset_size,
                    k=run.k,
                    metric_scope="ranking_only",
                    mean_runtime_ms=round(statistics.mean(ranking_times), 3),
                    median_runtime_ms=round(statistics.median(ranking_times), 3),
                    runs_data=ranking_times,
                    timestamp=timestamp,
                    notes="cache_disabled",
                )
            )
            results.append(
                BenchmarkResult(
                    algorithm=run.algorithm,
                    ranking_strategy=run.strategy,
                    dataset_size=run.dataset_size,
                    k=run.k,
                    metric_scope="end_to_end",
                    mean_runtime_ms=round(statistics.mean(end_to_end_times), 3),
                    median_runtime_ms=round(statistics.median(end_to_end_times), 3),
                    runs_data=end_to_end_times,
                    timestamp=timestamp,
                    notes="cache_disabled",
                )
            )

            outputs.append(
                {
                    "algorithm": run.algorithm,
                    "strategy": run.strategy,
                    "dataset_size": run.dataset_size,
                    "k": run.k,
                    "top_ids": top_ids,
                    "fallback_applied": fallback_applied,
                }
            )

        stats = {
            "source_rows": len(self.dataset.products),
            "active_features": self.dataset.active_features,
            "dropped_rows": self.dataset.dropped_rows,
            "source_path": str(self.dataset.source_path),
        }
        return results, outputs, stats
