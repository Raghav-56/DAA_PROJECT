from __future__ import annotations

import pandas as pd


class Normalizer:
    EPSILON = 1e-12
    COST_FEATURES = {"price", "delivery_time"}

    def normalize(
        self, df: pd.DataFrame, active_features: list[str]
    ) -> tuple[pd.DataFrame, dict[str, dict[str, float]]]:
        out = df.copy()
        stats: dict[str, dict[str, float]] = {}

        for feature in active_features:
            minimum = float(out[feature].min())
            maximum = float(out[feature].max())
            denom = (maximum - minimum) + self.EPSILON
            normalized = (out[feature] - minimum) / denom

            if feature in self.COST_FEATURES:
                normalized = 1.0 - normalized

            out[f"{feature}_norm"] = normalized.clip(0.0, 1.0)
            stats[feature] = {
                "min": minimum,
                "max": maximum,
                "epsilon": self.EPSILON,
            }

        return out, stats
