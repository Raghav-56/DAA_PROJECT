from __future__ import annotations

import pandas as pd


class FeatureActivator:
    MANDATORY = ["price", "rating"]
    OPTIONAL = ["discount", "reviews_count", "delivery_time"]

    def activate(
        self, df: pd.DataFrame, delivery_parse_success: float
    ) -> tuple[list[str], dict[str, str]]:
        active: list[str] = []
        reasons: dict[str, str] = {}

        for feature in self.MANDATORY:
            if feature not in df.columns:
                reasons[feature] = "missing_mandatory"
                continue
            variation = float(df[feature].max() - df[feature].min())
            if variation <= 1e-12:
                reasons[feature] = "degenerate_mandatory"
                continue
            active.append(feature)
            reasons[feature] = "active_mandatory"

        for feature in self.OPTIONAL:
            if feature not in df.columns:
                reasons[feature] = "missing"
                continue

            variation = float(df[feature].max() - df[feature].min())
            if variation <= 1e-12:
                reasons[feature] = "inactive_zero_variance"
                continue

            if feature == "delivery_time" and delivery_parse_success <= 0.95:
                reasons[feature] = "inactive_parse_success_below_95pct"
                continue

            active.append(feature)
            reasons[feature] = "active_optional"

        return active, reasons
