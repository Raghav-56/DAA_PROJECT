from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from Src.common.errors import MissingRequiredParamError

REQUIRED_COLUMNS = ["product_rating", "discounted_price"]
OPTIONAL_COLUMNS = [
    "product_id",
    "discount_percentage",
    "total_reviews",
    "delivery_date",
    "product_category",
]


class DatasetLoader:
    def __init__(self, csv_path: str | Path) -> None:
        self.csv_path = Path(csv_path)

    def compute_hash(self) -> str:
        digest = hashlib.sha256()
        with self.csv_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def load(self) -> pd.DataFrame:
        if not self.csv_path.exists():
            raise MissingRequiredParamError(f"Dataset file not found: {self.csv_path}")

        df = pd.read_csv(self.csv_path)

        missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
        if missing:
            raise MissingRequiredParamError(
                f"Dataset missing required columns: {missing}"
            )

        if "product_id" not in df.columns:
            df["product_id"] = [f"row_{index:06d}" for index in range(len(df))]

        return df

    @staticmethod
    def detect_optional_columns(df: pd.DataFrame) -> list[str]:
        return [column for column in OPTIONAL_COLUMNS if column in df.columns]
