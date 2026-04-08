from __future__ import annotations

import re

import numpy as np
import pandas as pd


class Preprocessor:
    NUMERIC_COLUMN_MAP = {
        "rating": "product_rating",
        "price": "discounted_price",
        "discount": "discount_percentage",
        "reviews_count": "total_reviews",
    }

    @staticmethod
    def _parse_delivery_days(series: pd.Series) -> pd.Series:
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().mean() > 0.95:
            return numeric

        extracted = series.astype(str).str.extract(r"(\d+(?:\.\d+)?)")[0]
        parsed = pd.to_numeric(extracted, errors="coerce")
        return parsed

    def clean(self, df: pd.DataFrame) -> tuple[pd.DataFrame, int, float]:
        out = df.copy()
        out["row_uid"] = np.arange(len(out), dtype=int)

        for target, source in self.NUMERIC_COLUMN_MAP.items():
            if source in out.columns:
                out[target] = pd.to_numeric(out[source], errors="coerce")
            else:
                out[target] = np.nan

        if "delivery_date" in out.columns:
            out["delivery_time"] = self._parse_delivery_days(out["delivery_date"])
            parse_success = float(out["delivery_time"].notna().mean())
        else:
            out["delivery_time"] = np.nan
            parse_success = 0.0

        out.replace([np.inf, -np.inf], np.nan, inplace=True)

        numeric_features = [
            "rating",
            "price",
            "discount",
            "reviews_count",
            "delivery_time",
        ]
        for feature in numeric_features:
            if feature not in out.columns:
                continue
            non_missing = out[feature].dropna()
            if not non_missing.empty:
                out[feature] = out[feature].fillna(non_missing.median())

        before = len(out)
        out = out.dropna(subset=["rating", "price"]).copy()
        dropped_rows = before - len(out)

        if "product_id" not in out.columns:
            out["product_id"] = [f"row_{row_uid:06d}" for row_uid in out["row_uid"]]
        else:
            out["product_id"] = out["product_id"].fillna(
                out["row_uid"].map(lambda row_uid: f"row_{row_uid:06d}")
            )

        out["product_id"] = out["product_id"].astype(str)
        out["category"] = out.get("product_category")

        columns = [
            "product_id",
            "row_uid",
            "rating",
            "price",
            "discount",
            "reviews_count",
            "delivery_time",
            "category",
        ]
        return out[columns], dropped_rows, parse_success
