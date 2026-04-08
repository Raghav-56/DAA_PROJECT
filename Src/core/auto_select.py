from __future__ import annotations



def select_algorithm(
    algorithm: str,
    k: int,
    n: int,
    quick_sort_fraction_threshold: float = 0.30,
    heap_preferred_k_threshold: int = 1000,
) -> str:
    if algorithm != "auto":
        return algorithm

    if n <= 0:
        return "quick_sort"

    if k > quick_sort_fraction_threshold * n:
        return "quick_sort"

    if k <= heap_preferred_k_threshold:
        return "heap_top_k"

    return "quick_sort"
