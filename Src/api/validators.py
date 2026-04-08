from __future__ import annotations

from Src.common.errors import (
    AttributeNotFoundError,
    InvalidAlgorithmError,
    InvalidStrategyError,
    MissingRequiredParamError,
)
from Src.common.models import ALLOWED_RETURN_FIELDS, RankRequest


REQUIRED_STRATEGY_FIELDS = {
    "single_asc": "attribute",
    "single_desc": "attribute",
    "lexicographic": "priority",
    "weighted": "weights",
}


ALLOWED_ALGORITHMS = {"merge_sort", "quick_sort", "heap_top_k", "auto"}
ALLOWED_STRATEGIES = set(REQUIRED_STRATEGY_FIELDS)


def validate_rank_request(payload: RankRequest) -> None:
    if payload.strategy not in ALLOWED_STRATEGIES:
        allowed = ", ".join(sorted(ALLOWED_STRATEGIES))
        raise InvalidStrategyError(
            f"Strategy '{payload.strategy}' not recognized. "
            f"Valid options: {allowed}"
        )

    required_key = REQUIRED_STRATEGY_FIELDS[payload.strategy]
    if required_key not in payload.strategy_params:
        raise MissingRequiredParamError(
            f"Missing required strategy parameter '{required_key}' "
            f"for strategy '{payload.strategy}'"
        )

    if payload.strategy in {"single_asc", "single_desc"}:
        if not isinstance(payload.strategy_params.get("attribute"), str):
            raise MissingRequiredParamError(
                "strategy_params.attribute must be a string"
            )

    if payload.strategy == "lexicographic":
        priority = payload.strategy_params.get("priority")
        if not isinstance(priority, list) or not priority:
            raise MissingRequiredParamError(
                "strategy_params.priority must be a non-empty list"
            )

    if payload.strategy == "weighted":
        weights = payload.strategy_params.get("weights")
        if not (weights == "default" or isinstance(weights, dict)):
            raise MissingRequiredParamError(
                "strategy_params.weights must be 'default' or an object"
            )

    if payload.algorithm not in ALLOWED_ALGORITHMS:
        raise InvalidAlgorithmError(
            "Algorithm must be one of merge_sort, quick_sort, heap_top_k, auto"
        )

    unknown: list[str] = []
    for field in payload.return_fields:
        if field not in ALLOWED_RETURN_FIELDS:
            unknown.append(field)
    if unknown:
        raise AttributeNotFoundError(f"Unknown return_fields: {unknown}")
