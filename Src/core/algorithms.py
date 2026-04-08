from __future__ import annotations

import heapq
from dataclasses import dataclass

from Src.core.comparator import DeterministicComparator
from Src.core.types import ProductRecord


class MergeSortRanker:
    def rank(
        self,
        products: list[ProductRecord],
        comparator: DeterministicComparator,
        k: int | None = None,
    ) -> list[ProductRecord]:
        sorted_products = self._merge_sort(products, comparator)
        return sorted_products if k is None else sorted_products[:k]

    def _merge_sort(
        self, products: list[ProductRecord], comparator: DeterministicComparator
    ) -> list[ProductRecord]:
        if len(products) <= 1:
            return products

        mid = len(products) // 2
        left = self._merge_sort(products[:mid], comparator)
        right = self._merge_sort(products[mid:], comparator)
        return self._merge(left, right, comparator)

    @staticmethod
    def _merge(
        left: list[ProductRecord],
        right: list[ProductRecord],
        comparator: DeterministicComparator,
    ) -> list[ProductRecord]:
        merged: list[ProductRecord] = []
        i = 0
        j = 0

        while i < len(left) and j < len(right):
            if comparator.compare_fn(left[i], right[j]) <= 0:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1

        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged


class QuickSortRanker:
    def rank(
        self,
        products: list[ProductRecord],
        comparator: DeterministicComparator,
        k: int | None = None,
    ) -> list[ProductRecord]:
        items = list(products)
        self._quick_sort(items, 0, len(items) - 1, comparator)
        return items if k is None else items[:k]

    def _quick_sort(
        self,
        products: list[ProductRecord],
        low: int,
        high: int,
        comparator: DeterministicComparator,
    ) -> None:
        if low < high:
            pivot = self._partition(products, low, high, comparator)
            self._quick_sort(products, low, pivot - 1, comparator)
            self._quick_sort(products, pivot + 1, high, comparator)

    def _partition(
        self,
        products: list[ProductRecord],
        low: int,
        high: int,
        comparator: DeterministicComparator,
    ) -> int:
        mid = low + (high - low) // 2
        pivot_idx = self._median_of_three(products, low, mid, high, comparator)
        products[pivot_idx], products[high] = products[high], products[pivot_idx]
        pivot = products[high]

        i = low - 1
        for j in range(low, high):
            if comparator.compare_fn(products[j], pivot) < 0:
                i += 1
                products[i], products[j] = products[j], products[i]

        products[i + 1], products[high] = products[high], products[i + 1]
        return i + 1

    @staticmethod
    def _median_of_three(
        products: list[ProductRecord],
        a: int,
        b: int,
        c: int,
        comparator: DeterministicComparator,
    ) -> int:
        if comparator.compare_fn(products[a], products[b]) < 0:
            if comparator.compare_fn(products[b], products[c]) < 0:
                return b
            if comparator.compare_fn(products[a], products[c]) < 0:
                return c
            return a

        if comparator.compare_fn(products[a], products[c]) < 0:
            return a
        if comparator.compare_fn(products[b], products[c]) < 0:
            return c
        return b


@dataclass(slots=True)
class _HeapItem:
    product: ProductRecord
    comparator: DeterministicComparator

    def __lt__(self, other: "_HeapItem") -> bool:
        return self.comparator.compare_fn(self.product, other.product) > 0


class HeapTopKRanker:
    def rank(
        self,
        products: list[ProductRecord],
        comparator: DeterministicComparator,
        k: int | None = None,
    ) -> list[ProductRecord]:
        if not k or k >= len(products):
            return sorted(products, key=comparator.get_sort_key())

        heap: list[_HeapItem] = []
        for product in products:
            item = _HeapItem(product=product, comparator=comparator)
            if len(heap) < k:
                heapq.heappush(heap, item)
                continue

            worst = heap[0].product
            if comparator.compare_fn(product, worst) < 0:
                heapq.heapreplace(heap, item)

        result = [item.product for item in heap]
        result.sort(key=comparator.get_sort_key())
        return result
