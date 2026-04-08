from __future__ import annotations

from dataclasses import dataclass

from Src.common.errors import InactiveAttributeUnavailableError, InvalidStrategyError
from Src.core.scoring import compute_composite_score, renormalize_weights
from Src.core.types import ProductRecord


COST_FEATURES = {"price", "delivery_time"}


class RankingStrategy:
    strategy_name: str
    score_type: str

    def prepare_products(self, products: list[ProductRecord]) -> None:
        return None


@dataclass(slots=True)
class SingleAscStrategy(RankingStrategy):
    attribute: str
    strategy_name: str = "single_asc"
    score_type: str = "single_attribute"

    def prepare_products(self, products: list[ProductRecord]) -> None:
        for product in products:
            product.primary_score = product.value_for(self.attribute)
            product.score_type = self.score_type


@dataclass(slots=True)
class SingleDescStrategy(RankingStrategy):
    attribute: str
    strategy_name: str = "single_desc"
    score_type: str = "single_attribute"

    def prepare_products(self, products: list[ProductRecord]) -> None:
        for product in products:
            product.primary_score = product.value_for(self.attribute)
            product.score_type = self.score_type


@dataclass(slots=True)
class LexicographicStrategy(RankingStrategy):
    priority: list[str]
    strategy_name: str = "lexicographic"
    score_type: str = "lexicographic"

    def prepare_products(self, products: list[ProductRecord]) -> None:
        for product in products:
            product.primary_score = None
            product.score_type = self.score_type
            product.ranking_keys = [product.value_for(feature) for feature in self.priority]


@dataclass(slots=True)
class WeightedStrategy(RankingStrategy):
    weights: dict[str, float] | str
    active_features: list[str]
    strategy_name: str = "weighted"
    score_type: str = "weighted_composite"

    def prepare_products(self, products: list[ProductRecord]) -> None:
        for product in products:
            composite = compute_composite_score(
                product, self.active_features, self.weights
            )
            product.primary_score = composite.value
            product.score_type = self.score_type

    def active_weights(self) -> dict[str, float]:
        return renormalize_weights(self.weights, self.active_features)



def _require_active(
    attributes: list[str], active_features: list[str], allow_fallback: bool
) -> bool:
    missing = [attribute for attribute in attributes if attribute not in active_features]
    if missing and not allow_fallback:
        raise InactiveAttributeUnavailableError(
            f"Inactive attributes requested: {missing}"
        )
    return bool(missing)



def build_strategy(
    strategy: str,
    strategy_params: dict,
    active_features: list[str],
    allow_fallback: bool = False,
) -> tuple[RankingStrategy, bool]:
    fallback_applied = False

    if strategy == "single_asc":
        attribute = str(strategy_params["attribute"])
        fallback_applied = _require_active([attribute], active_features, allow_fallback)
        if fallback_applied:
            return WeightedStrategy("default", active_features), True
        return SingleAscStrategy(attribute=attribute), False

    if strategy == "single_desc":
        attribute = str(strategy_params["attribute"])
        fallback_applied = _require_active([attribute], active_features, allow_fallback)
        if fallback_applied:
            return WeightedStrategy("default", active_features), True
        return SingleDescStrategy(attribute=attribute), False

    if strategy == "lexicographic":
        priority = [str(item) for item in strategy_params["priority"]]
        fallback_applied = _require_active(priority, active_features, allow_fallback)
        if fallback_applied:
            return WeightedStrategy("default", active_features), True
        return LexicographicStrategy(priority=priority), False

    if strategy == "weighted":
        weights = strategy_params.get("weights", "default")
        return WeightedStrategy(weights=weights, active_features=active_features), False

    raise InvalidStrategyError(
        f"Strategy '{strategy}' not recognized. Valid options: single_asc, single_desc, lexicographic, weighted"
    )
