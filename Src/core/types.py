from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ProductRecord:
    product_id: str
    row_uid: int
    rating: float
    price: float
    discount: float | None
    reviews_count: float | None
    delivery_time: float | None
    category: str | None = None
    primary_score: float | None = None
    score_type: str = "single_attribute"
    ranking_keys: list[float] | None = None
    normalized: dict[str, float] = field(default_factory=dict)

    def value_for(self, feature: str) -> float:
        mapping: dict[str, float | None] = {
            "rating": self.rating,
            "price": self.price,
            "discount": self.discount,
            "reviews_count": self.reviews_count,
            "delivery_time": self.delivery_time,
        }
        value = mapping.get(feature)
        return 0.0 if value is None else float(value)


@dataclass(slots=True)
class PreprocessedDataset:
    products: list[ProductRecord]
    active_features: list[str]
    feature_reasons: dict[str, str]
    normalization_stats: dict[str, dict[str, float]]
    dropped_rows: int
    source_path: Path
    dataset_hash: str


@dataclass(slots=True)
class RankingResult:
    ranked_products: list[ProductRecord]
    algorithm_used: str
    algorithm_time_ms: float
    cache_hit: bool = False
    cache_key: str | None = None
    fallback_applied: bool = False
    active_weights: dict[str, float] | None = None


@dataclass(slots=True)
class BenchmarkRun:
    algorithm: str
    strategy: str
    strategy_params: dict[str, Any]
    dataset_size: int
    k: int


@dataclass(slots=True)
class BenchmarkResult:
    algorithm: str
    ranking_strategy: str
    dataset_size: int
    k: int
    metric_scope: str
    mean_runtime_ms: float
    median_runtime_ms: float
    runs_data: list[float]
    timestamp: str
    notes: str = ""


@dataclass(slots=True)
class ValidationReport:
    is_valid: bool
    error_count: int
    mismatches: list[str]
