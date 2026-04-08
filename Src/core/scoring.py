from __future__ import annotations

from collections import namedtuple

from Src.core.types import ProductRecord


CompositeScore = namedtuple("CompositeScore", ["value", "breakdown"])

DEFAULT_BASE_WEIGHTS = {
    "rating": 0.40,
    "price": 0.30,
    "discount": 0.15,
    "reviews_count": 0.10,
    "delivery_time": 0.05,
}



def renormalize_weights(
    weights: dict[str, float] | str, active_features: list[str]
) -> dict[str, float]:
    base = DEFAULT_BASE_WEIGHTS if weights == "default" else dict(weights)
    denominator = sum(base.get(feature, 0.0) for feature in active_features)
    if denominator <= 0:
        return {feature: 0.0 for feature in active_features}
    return {
        feature: base.get(feature, 0.0) / denominator
        for feature in active_features
        if feature in base
    }



def compute_composite_score(
    product: ProductRecord,
    active_features: list[str],
    weights: dict[str, float] | str,
) -> CompositeScore:
    active_weights = renormalize_weights(weights, active_features)
    breakdown: dict[str, float] = {}
    total = 0.0

    for feature in active_features:
        value = product.normalized.get(feature, 0.0)
        contribution = active_weights.get(feature, 0.0) * value
        breakdown[feature] = round(contribution, 12)
        total += contribution

    return CompositeScore(round(total, 12), breakdown)
