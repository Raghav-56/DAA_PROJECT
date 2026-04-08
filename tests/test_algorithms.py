from __future__ import annotations

import pytest

from Src.core.comparator import DeterministicComparator
from Src.core.engine import RankingEngine
from Src.core.pipeline import preprocess_dataset
from Src.core.strategies import SingleDescStrategy


@pytest.mark.smoke
def test_merge_and_quick_equivalence_top_k() -> None:
    dataset = preprocess_dataset(
        "Dataset/amazon_products_sales_data/amazon_products_sales_data_cleaned.csv"
    )
    strategy = SingleDescStrategy(attribute="rating")
    comparator = DeterministicComparator(strategy, dataset.active_features)
    engine = RankingEngine(dataset, strategy, comparator)

    merge = engine.rank(k=100, algorithm="merge_sort", use_cache=False)
    quick = engine.rank(k=100, algorithm="quick_sort", use_cache=False)
    heap = engine.rank(k=100, algorithm="heap_top_k", use_cache=False)

    merge_ids = [p.product_id for p in merge.ranked_products]
    quick_ids = [p.product_id for p in quick.ranked_products]
    heap_ids = [p.product_id for p in heap.ranked_products]

    assert merge_ids == quick_ids
    assert heap_ids == merge_ids[:100]
