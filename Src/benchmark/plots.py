from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

from Src.core.types import BenchmarkResult



def _filter_ranking_only(results: list[BenchmarkResult]) -> list[BenchmarkResult]:
    return [result for result in results if result.metric_scope == "ranking_only"]



def plot_runtime_scaling(results: list[BenchmarkResult], output_path: Path) -> None:
    data = _filter_ranking_only(results)
    grouped: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))

    for row in data:
        grouped[row.algorithm][row.dataset_size].append(row.mean_runtime_ms)

    fig, ax = plt.subplots(figsize=(9, 5))
    for algorithm, size_map in sorted(grouped.items()):
        xs = sorted(size_map)
        ys = [sum(size_map[x]) / len(size_map[x]) for x in xs]
        ax.plot(xs, ys, marker="o", label=algorithm)

    ax.set_title("Runtime Scaling by Algorithm")
    ax.set_xlabel("Dataset Size")
    ax.set_ylabel("Mean Runtime (ms)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)



def plot_algorithm_comparison(results: list[BenchmarkResult], output_path: Path) -> None:
    data = _filter_ranking_only(results)
    strategy_algo: dict[tuple[str, str], list[float]] = defaultdict(list)

    for row in data:
        strategy_algo[(row.ranking_strategy, row.algorithm)].append(row.mean_runtime_ms)

    strategies = sorted({row.ranking_strategy for row in data})
    algorithms = sorted({row.algorithm for row in data})

    fig, ax = plt.subplots(figsize=(10, 5))
    width = 0.2
    x_positions = list(range(len(strategies)))

    for offset, algorithm in enumerate(algorithms):
        values = [
            sum(strategy_algo[(strategy, algorithm)])
            / max(1, len(strategy_algo[(strategy, algorithm)]))
            for strategy in strategies
        ]
        shifted = [x + (offset - 1) * width for x in x_positions]
        ax.bar(shifted, values, width=width, label=algorithm)

    ax.set_title("Algorithm Comparison Across Strategies")
    ax.set_xlabel("Strategy")
    ax.set_ylabel("Mean Runtime (ms)")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(strategies, rotation=15)
    ax.grid(axis="y", alpha=0.3)
    ax.legend()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)



def plot_speedup(results: list[BenchmarkResult], output_path: Path) -> None:
    data = _filter_ranking_only(results)
    strategy_algo: dict[tuple[str, str], list[float]] = defaultdict(list)

    for row in data:
        strategy_algo[(row.ranking_strategy, row.algorithm)].append(row.mean_runtime_ms)

    strategies = sorted({row.ranking_strategy for row in data})
    targets = ["quick_sort", "heap_top_k"]

    fig, ax = plt.subplots(figsize=(9, 5))
    width = 0.35
    x_positions = list(range(len(strategies)))

    for offset, algorithm in enumerate(targets):
        speedups: list[float] = []
        for strategy in strategies:
            baseline_values = strategy_algo[(strategy, "merge_sort")]
            target_values = strategy_algo[(strategy, algorithm)]
            baseline = sum(baseline_values) / max(1, len(baseline_values))
            target = sum(target_values) / max(1, len(target_values))
            speedups.append(0.0 if target == 0 else round(baseline / target, 3))

        shifted = [x + (offset - 0.5) * width for x in x_positions]
        ax.bar(shifted, speedups, width=width, label=f"merge/{algorithm}")

    ax.set_title("Speedup Relative to Merge Sort")
    ax.set_xlabel("Strategy")
    ax.set_ylabel("Speedup Ratio")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(strategies, rotation=15)
    ax.grid(axis="y", alpha=0.3)
    ax.legend()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
