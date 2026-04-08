from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from Src.core.types import BenchmarkResult, ValidationReport



def ensure_output_dirs(base: Path = Path("outputs")) -> dict[str, Path]:
    benchmarks = base / "benchmarks"
    rankings = base / "rankings"
    reports = base / "reports"
    benchmarks.mkdir(parents=True, exist_ok=True)
    rankings.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    return {
        "base": base,
        "benchmarks": benchmarks,
        "rankings": rankings,
        "reports": reports,
    }



def write_benchmark_csv(results: list[BenchmarkResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "algorithm",
                "ranking_strategy",
                "dataset_size",
                "k",
                "metric_scope",
                "mean_runtime_ms",
                "median_runtime_ms",
                "timestamp",
                "notes",
            ]
        )
        for row in results:
            writer.writerow(
                [
                    row.algorithm,
                    row.ranking_strategy,
                    row.dataset_size,
                    row.k,
                    row.metric_scope,
                    row.mean_runtime_ms,
                    row.median_runtime_ms,
                    row.timestamp,
                    row.notes,
                ]
            )



def read_benchmark_csv(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader)



def write_ranked_products_json(
    ranked_products: list[dict[str, Any]],
    strategy: str,
    algorithm: str,
    dataset_size: int,
    k: int,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "strategy": strategy,
        "algorithm": algorithm,
        "dataset_size": dataset_size,
        "k": k,
        "ranked_products": ranked_products,
    }
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)



def write_correctness_report(
    validation_report: ValidationReport,
    output_path: Path,
    title: str = "Validation Report",
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {title}",
        "",
        f"- is_valid: {validation_report.is_valid}",
        f"- error_count: {validation_report.error_count}",
        "",
        "## mismatches",
    ]

    if validation_report.mismatches:
        lines.extend(f"- {item}" for item in validation_report.mismatches)
    else:
        lines.append("- none")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
