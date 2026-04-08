from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from Src.api.validators import validate_rank_request
from Src.common.errors import RankingError
from Src.common.models import CacheClearResponse, RankRequest, RankResponse
from Src.common.utils import error_response, get_iso8601_timestamp
from Src.core.comparator import DeterministicComparator
from Src.core.engine import RankingEngine
from Src.core.pipeline import preprocess_dataset
from Src.core.strategies import build_strategy

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "timestamp": get_iso8601_timestamp()}


def _build_ranked_product_row(product: Any, return_fields: list[str]) -> dict[str, Any]:
    row: dict[str, Any] = {
        "product_id": product.product_id,
        "primary_score": product.primary_score,
        "score_type": product.score_type,
    }
    if "ranking_keys" in return_fields and product.ranking_keys is not None:
        row["ranking_keys"] = product.ranking_keys
    if "rating" in return_fields:
        row["rating"] = product.rating
    if "price" in return_fields:
        row["price"] = product.price
    if "discount" in return_fields:
        row["discount"] = product.discount
    if "reviews_count" in return_fields:
        row["reviews_count"] = product.reviews_count
    if "delivery_time" in return_fields:
        row["delivery_time"] = product.delivery_time
    return row


def _authorize_cache_admin(request: Request) -> bool:
    admin_token = request.app.state.settings.cache_admin_token
    if not admin_token:
        return True
    auth = request.headers.get("Authorization", "")
    return auth == f"Bearer {admin_token}"


@router.post("/rank")
def rank(payload: RankRequest, request: Request) -> RankResponse | JSONResponse:
    try:
        total_start = time.perf_counter()
        validate_rank_request(payload)

        settings = request.app.state.settings
        cache = request.app.state.cache
        tracker = request.app.state.dataset_tracker

        if tracker.has_changed():
            request.app.state.dataset = None
            if cache is not None:
                cache.clear_all()

        dataset = request.app.state.dataset
        if dataset is None:
            dataset = preprocess_dataset(settings.dataset_path)
            request.app.state.dataset = dataset

        strategy, fallback_applied = build_strategy(
            payload.strategy,
            payload.strategy_params,
            dataset.active_features,
            allow_fallback=payload.allow_fallback,
        )

        comparator = DeterministicComparator(strategy, dataset.active_features)
        engine = RankingEngine(dataset, strategy, comparator, cache=cache)
        result = engine.rank(
            k=payload.k,
            algorithm=payload.algorithm,
            use_cache=payload.use_cache,
            strategy_name=payload.strategy,
            strategy_params=payload.strategy_params,
            quick_sort_fraction_threshold=settings.quick_sort_fraction_threshold,
            heap_preferred_k_threshold=settings.heap_preferred_k_threshold,
        )

        result.fallback_applied = fallback_applied
        ranked_rows = [
            _build_ranked_product_row(product, payload.return_fields)
            for product in result.ranked_products
        ]
        total_time_ms = round((time.perf_counter() - total_start) * 1000.0, 3)

        return RankResponse(
            algorithm_used=result.algorithm_used,
            strategy=payload.strategy,
            k=payload.k,
            ranked_products=ranked_rows,
            execution_metrics={
                "algorithm_time_ms": result.algorithm_time_ms,
                "total_time_ms": total_time_ms,
                "cache_hit": result.cache_hit,
                "cache_key": result.cache_key,
            },
            metadata={
                "timestamp": get_iso8601_timestamp(),
                "dataset_rows_used": len(dataset.products),
                "effective_k": len(result.ranked_products),
                "fallback_applied": fallback_applied,
                "active_features": dataset.active_features,
                "active_weights": result.active_weights,
            },
        )
    except RankingError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(exc.error_code, exc.message),
        )


@router.post("/cache/clear")
def clear_cache_all(request: Request) -> CacheClearResponse | JSONResponse:
    if not _authorize_cache_admin(request):
        return JSONResponse(
            status_code=401,
            content=error_response("internal_error", "Unauthorized cache clear request"),
        )

    cache = request.app.state.cache
    if cache is None:
        return CacheClearResponse(
            status="success",
            cleared_entries=0,
            timestamp=get_iso8601_timestamp(),
        )

    cleared = cache.clear_all()
    return CacheClearResponse(
        status="success",
        cleared_entries=cleared,
        timestamp=get_iso8601_timestamp(),
    )


@router.post("/cache/clear/{strategy}")
def clear_cache_strategy(
    strategy: str,
    request: Request,
) -> CacheClearResponse | JSONResponse:
    if not _authorize_cache_admin(request):
        return JSONResponse(
            status_code=401,
            content=error_response("internal_error", "Unauthorized cache clear request"),
        )

    cache = request.app.state.cache
    cleared = 0 if cache is None else cache.clear_strategy(strategy)
    return CacheClearResponse(
        status="success",
        cleared_entries=cleared,
        strategy=strategy,
        timestamp=get_iso8601_timestamp(),
    )
