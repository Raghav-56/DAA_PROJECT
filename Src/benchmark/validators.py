from __future__ import annotations

from collections import defaultdict

from Src.core.types import ValidationReport



def validate_merge_vs_quick(outputs: list[dict]) -> ValidationReport:
    grouped: dict[tuple[str, int, int], dict[str, list[str]]] = defaultdict(dict)
    mismatches: list[str] = []

    for item in outputs:
        key = (item["strategy"], item["dataset_size"], item["k"])
        grouped[key][item["algorithm"]] = item["top_ids"]

    for key, by_algo in grouped.items():
        merge_ids = by_algo.get("merge_sort")
        quick_ids = by_algo.get("quick_sort")
        if merge_ids is None or quick_ids is None:
            continue
        if merge_ids != quick_ids:
            mismatches.append(f"merge!=quick for {key}")

    return ValidationReport(
        is_valid=not mismatches,
        error_count=len(mismatches),
        mismatches=mismatches,
    )



def validate_heap_consistency(outputs: list[dict]) -> ValidationReport:
    grouped: dict[tuple[str, int, int], dict[str, list[str]]] = defaultdict(dict)
    mismatches: list[str] = []

    for item in outputs:
        key = (item["strategy"], item["dataset_size"], item["k"])
        grouped[key][item["algorithm"]] = item["top_ids"]

    for key, by_algo in grouped.items():
        merge_ids = by_algo.get("merge_sort")
        heap_ids = by_algo.get("heap_top_k")
        if merge_ids is None or heap_ids is None:
            continue
        if heap_ids != merge_ids[: len(heap_ids)]:
            mismatches.append(f"heap prefix mismatch for {key}")

    return ValidationReport(
        is_valid=not mismatches,
        error_count=len(mismatches),
        mismatches=mismatches,
    )



def validate_determinism(
    outputs_run1: list[dict], outputs_run2: list[dict]
) -> ValidationReport:
    index_run2 = {
        (
            item["algorithm"],
            item["strategy"],
            item["dataset_size"],
            item["k"],
        ): item["top_ids"]
        for item in outputs_run2
    }

    mismatches: list[str] = []
    for item in outputs_run1:
        key = (
            item["algorithm"],
            item["strategy"],
            item["dataset_size"],
            item["k"],
        )
        other = index_run2.get(key)
        if other is None:
            mismatches.append(f"missing run2 key {key}")
            continue
        if item["top_ids"] != other:
            mismatches.append(f"order drift {key}")

    return ValidationReport(
        is_valid=not mismatches,
        error_count=len(mismatches),
        mismatches=mismatches,
    )
