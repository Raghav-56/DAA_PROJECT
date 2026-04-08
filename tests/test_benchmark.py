from __future__ import annotations

import pytest

from Src.benchmark.matrix import BenchmarkMatrix
from Src.benchmark.runner import BenchmarkRunner
from Src.benchmark.validators import validate_merge_vs_quick


@pytest.mark.smoke
def test_benchmark_smoke_matrix_and_validator() -> None:
    matrix = BenchmarkMatrix()
    runs = matrix.get_smoke_runs()[:6]

    runner = BenchmarkRunner(
        "Dataset/amazon_products_sales_data/amazon_products_sales_data_cleaned.csv"
    )
    results, outputs, _stats = runner.run_matrix(runs)

    assert results
    assert outputs

    report = validate_merge_vs_quick(outputs)
    assert report.is_valid
