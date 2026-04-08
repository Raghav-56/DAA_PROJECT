from __future__ import annotations

from Src.core.types import BenchmarkRun


class BenchmarkMatrix:
    ALGORITHMS = ["merge_sort", "quick_sort", "heap_top_k"]
    STRATEGIES = {
        "single_desc": {"attribute": "rating"},
        "single_asc": {"attribute": "price"},
        "lexicographic": {"priority": ["rating", "price", "reviews_count"]},
        "weighted": {
            "weights": {
                "rating": 0.4,
                "price": 0.3,
                "discount": 0.15,
                "reviews_count": 0.1,
                "delivery_time": 0.05,
            }
        },
    }
    DATASET_SIZES = [1000, 5000, 10000, 42000]
    K_VALUES = [10, 100, 500]

    def get_all_runs(self) -> list[BenchmarkRun]:
        runs: list[BenchmarkRun] = []
        for algorithm in self.ALGORITHMS:
            for strategy in sorted(self.STRATEGIES):
                for dataset_size in self.DATASET_SIZES:
                    for k in self.K_VALUES:
                        runs.append(
                            BenchmarkRun(
                                algorithm=algorithm,
                                strategy=strategy,
                                strategy_params=self.STRATEGIES[strategy],
                                dataset_size=dataset_size,
                                k=k,
                            )
                        )
        runs.sort(
            key=lambda run: (
                run.algorithm,
                run.strategy,
                run.dataset_size,
                run.k,
            )
        )
        return runs

    def get_smoke_runs(self) -> list[BenchmarkRun]:
        allowed_sizes = {1000, 5000}
        allowed_k = {10, 100}
        return [
            run
            for run in self.get_all_runs()
            if run.dataset_size in allowed_sizes and run.k in allowed_k
        ]
