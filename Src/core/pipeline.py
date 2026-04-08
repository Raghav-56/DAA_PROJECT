from __future__ import annotations

from pathlib import Path

from Src.core.dataset import DatasetLoader
from Src.core.features import FeatureActivator
from Src.core.normalization import Normalizer
from Src.core.preprocessing import Preprocessor
from Src.core.types import PreprocessedDataset, ProductRecord



def preprocess_dataset(csv_path: str | Path) -> PreprocessedDataset:
    loader = DatasetLoader(csv_path)
    source_hash = loader.compute_hash()
    raw_df = loader.load()

    preprocessor = Preprocessor()
    cleaned_df, dropped_rows, parse_success = preprocessor.clean(raw_df)

    activator = FeatureActivator()
    active_features, reasons = activator.activate(cleaned_df, parse_success)

    normalizer = Normalizer()
    normalized_df, stats = normalizer.normalize(cleaned_df, active_features)

    products: list[ProductRecord] = []
    for row in normalized_df.itertuples(index=False):
        normalized_values = {
            feature: float(getattr(row, f"{feature}_norm"))
            for feature in active_features
            if hasattr(row, f"{feature}_norm")
        }

        products.append(
            ProductRecord(
                product_id=str(row.product_id),
                row_uid=int(row.row_uid),
                rating=float(row.rating),
                price=float(row.price),
                discount=float(row.discount) if row.discount == row.discount else None,
                reviews_count=(
                    float(row.reviews_count)
                    if row.reviews_count == row.reviews_count
                    else None
                ),
                delivery_time=(
                    float(row.delivery_time)
                    if row.delivery_time == row.delivery_time
                    else None
                ),
                category=(str(row.category) if row.category == row.category else None),
                normalized=normalized_values,
            )
        )

    return PreprocessedDataset(
        products=products,
        active_features=active_features,
        feature_reasons=reasons,
        normalization_stats=stats,
        dropped_rows=dropped_rows,
        source_path=Path(csv_path),
        dataset_hash=source_hash,
    )
