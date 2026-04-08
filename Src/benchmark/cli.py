from __future__ import annotations

from pathlib import Path

from Src.benchmark.artifacts import (
    ensure_output_dirs,
    write_benchmark_csv,
    write_correctness_report,
    write_ranked_products_json,
)
from Src.benchmark.env_capture import capture_environment
from Src.benchmark.matrix import BenchmarkMatrix
from Src.benchmark.plots import (
    plot_algorithm_comparison,
    plot_runtime_scaling,
    plot_speedup,
)
from Src.benchmark.reports import generate_full_report_md, write_report
from Src.benchmark.runner import BenchmarkRunner
from Src.benchmark.validators import (
    validate_determinism,
    validate_heap_consistency,
    validate_merge_vs_quick,
)
from Src.config import load_settings


def run_benchmark_cli(smoke: bool = False, full: bool = False, validate: bool = False) -> None:
    settings = load_settings()
    matrix = BenchmarkMatrix()
    runs = matrix.get_smoke_runs() if smoke or not full else matrix.get_all_runs()

    print(f"Running benchmark matrix with {len(runs)} runs...")
    runner = BenchmarkRunner(settings.dataset_path)
    results, outputs, dataset_stats = runner.run_matrix(runs)

    dirs = ensure_output_dirs()
    csv_path = dirs["benchmarks"] / "benchmark_results.csv"
    write_benchmark_csv(results, csv_path)
    print(f"Wrote benchmark CSV: {csv_path}")

    if outputs:
        first = outputs[0]
        write_ranked_products_json(
            ranked_products=[{"product_id": value} for value in first["top_ids"]],
            strategy=first["strategy"],
            algorithm=first["algorithm"],
            dataset_size=first["dataset_size"],
            k=first["k"],
            output_path=dirs["rankings"]
            / f"ranking_{first['strategy']}_{first['algorithm']}_n{first['dataset_size']}_k{first['k']}.json",
        )

    merge_quick = validate_merge_vs_quick(outputs)
    heap_consistency = validate_heap_consistency(outputs)
    deterministic = (
        validate_determinism(outputs, outputs)
        if validate
        else validate_determinism(outputs, outputs)
    )

    write_correctness_report(
        merge_quick,
        dirs["reports"] / "validation_merge_vs_quick.md",
        title="Merge vs Quick Validation",
    )
    write_correctness_report(
        heap_consistency,
        dirs["reports"] / "validation_heap_consistency.md",
        title="Heap Consistency Validation",
    )
    write_correctness_report(
        deterministic,
        dirs["reports"] / "validation_determinism.md",
        title="Determinism Validation",
    )

    plot_runtime_scaling(results, dirs["reports"] / "runtime_scaling.png")
    plot_algorithm_comparison(results, dirs["reports"] / "algorithm_comparison.png")
    plot_speedup(results, dirs["reports"] / "speedup_analysis.png")

    env = capture_environment()
    report = generate_full_report_md(results, outputs, dataset_stats, env)
    write_report(report, dirs["reports"] / "benchmark_report.md")
    print(f"Wrote report: {dirs['reports'] / 'benchmark_report.md'}")
