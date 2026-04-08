from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


StrategyName = Literal["single_asc", "single_desc", "lexicographic", "weighted"]
AlgorithmName = Literal["merge_sort", "quick_sort", "heap_top_k", "auto"]


ALLOWED_RETURN_FIELDS = {
    "product_id",
    "primary_score",
    "score_type",
    "ranking_keys",
    "rating",
    "price",
    "discount",
    "reviews_count",
    "delivery_time",
}

DEFAULT_RETURN_FIELDS = ["product_id", "primary_score", "score_type"]


class RankRequest(BaseModel):
    strategy: StrategyName
    strategy_params: dict[str, Any] = Field(default_factory=dict)
    algorithm: AlgorithmName = "auto"
    k: int = 100
    return_fields: list[str] = Field(default_factory=lambda: list(DEFAULT_RETURN_FIELDS))
    allow_fallback: bool = False
    use_cache: bool = True

    @field_validator("k")
    @classmethod
    def validate_k(cls, value: int) -> int:
        if value < 1 or value > 42000:
            raise ValueError("k must be between 1 and 42000")
        return value

    @field_validator("return_fields")
    @classmethod
    def validate_return_fields(cls, fields: list[str]) -> list[str]:
        unknown = [field for field in fields if field not in ALLOWED_RETURN_FIELDS]
        if unknown:
            raise ValueError(f"Unknown return_fields: {unknown}")
        return fields


class RankedProduct(BaseModel):
    model_config = ConfigDict(extra="allow")

    product_id: str | int
    primary_score: float | None
    score_type: str
    ranking_keys: list[Any] | None = None


class ExecutionMetrics(BaseModel):
    algorithm_time_ms: float
    total_time_ms: float
    cache_hit: bool = False
    cache_key: str | None = None


class ResponseMetadata(BaseModel):
    timestamp: str
    dataset_rows_used: int
    effective_k: int
    fallback_applied: bool
    active_features: list[str]
    active_weights: dict[str, float] | None = None


class RankResponse(BaseModel):
    status: Literal["success"] = "success"
    algorithm_used: Literal["merge_sort", "quick_sort", "heap_top_k"]
    strategy: StrategyName
    k: int
    ranked_products: list[RankedProduct]
    execution_metrics: ExecutionMetrics
    metadata: ResponseMetadata


class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    error_code: str
    message: str
    timestamp: str


class CacheClearResponse(BaseModel):
    status: Literal["success"] = "success"
    cleared_entries: int
    timestamp: str
    strategy: str | None = None
