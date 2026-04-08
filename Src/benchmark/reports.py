from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from Src.core.types import BenchmarkResult



def generate_algorithm_comparison_md(results: list[BenchmarkResult]) -> str:
    ranking_only = [r for r in results if r.metric_scope == "ranking_only"]
    strategies = sorted({r.ranking_strategy for r in ranking_only})

    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in ranking_only:
        grouped[(row.ranking_strategy, row.algorithm)].append(row.mean_runtime_ms)

    lines = [
        "## Algorithm Comparison",
        "",
        "| Strategy | Merge Sort (ms) | Quick Sort (ms) | Heap Top-K (ms) | Fastest |",
        "|---|---:|---:|---:|---|",
    ]

    for strategy in strategies:
        merge = _avg(grouped[(strategy, "merge_sort")])
        quick = _avg(grouped[(strategy, "quick_sort")])
        heap = _avg(grouped[(strategy, "heap_top_k")])
        fastest = min(
            [("Merge", merge), ("Quick", quick), ("Heap", heap)],
            key=lambda item: item[1],
        )[0]
        lines.append(f"| {strategy} | {merge:.3f} | {quick:.3f} | {heap:.3f} | {fastest} |")

    return "\n".join(lines)



def generate_strategy_summary_md(outputs: list[dict]) -> str:
    lines = ["## Strategy Execution Summary", ""]
    by_strategy: dict[str, list[dict]] = defaultdict(list)
    for item in outputs:
        by_strategy[item["strategy"]].append(item)

    for strategy in sorted(by_strategy):
        lines.append(f"### {strategy}")
        sample = by_strategy[strategy][0]
        lines.append(f"- sample_top_5_ids: {sample['top_ids'][:5]}")
        lines.append("")

    return "\n".join(lines)



def generate_implementation_summary_md(
    dataset_stats: dict,
    preprocessing_summary: dict,
    environment_info: dict,
) -> str:
    lines = [
        "## Implementation Summary",
        "",
        f"- source_rows: {dataset_stats.get('source_rows')}",
        f"- active_features: {dataset_stats.get('active_features')}",
        f"- dropped_rows: {dataset_stats.get('dropped_rows')}",
        f"- source_path: {dataset_stats.get('source_path')}",
        f"- preprocessing: {preprocessing_summary}",
        f"- environment: {environment_info}",
    ]
    return "\n".join(lines)



def generate_full_report_md(
    results: list[BenchmarkResult],
    outputs: list[dict],
    dataset_stats: dict,
    environment_info: dict,
) -> str:
    sections = [
        "# Benchmark Report",
        "",
        generate_algorithm_comparison_md(results),
        "",
        generate_strategy_summary_md(outputs),
        "",
        generate_implementation_summary_md(
            dataset_stats,
            preprocessing_summary={"note": "median imputation + minmax normalization"},
            environment_info=environment_info,
        ),
        "",
    ]
    return "\n".join(sections)



def write_report(markdown: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")



def _avg(values: list[float]) -> float:
    return 0.0 if not values else sum(values) / len(values)
