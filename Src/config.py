from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(slots=True)
class Settings:
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    workers: int = 1
    dataset_path: Path = Path("Dataset/amazon_products_sales_data/amazon_products_sales_data_cleaned.csv")
    cache_enabled: bool = True
    max_cache_size_mb: int = 100
    cache_ttl_seconds: int = 3600
    cache_admin_token: str = ""
    heap_preferred_k_threshold: int = 1000
    quick_sort_fraction_threshold: float = 0.30



def _as_bool(raw: str | None, default: bool) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}



def load_settings() -> Settings:
    return Settings(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "5000")),
        debug=_as_bool(os.getenv("DEBUG"), False),
        workers=int(os.getenv("WORKERS", "1")),
        dataset_path=Path(os.getenv("DATASET_PATH", "Dataset/amazon_products_sales_data/amazon_products_sales_data_cleaned.csv")),
        cache_enabled=_as_bool(os.getenv("CACHE_ENABLED"), True),
        max_cache_size_mb=int(os.getenv("MAX_CACHE_SIZE_MB", "100")),
        cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "3600")),
        cache_admin_token=os.getenv("CACHE_ADMIN_TOKEN", ""),
        heap_preferred_k_threshold=int(os.getenv("HEAP_PREFERRED_K_THRESHOLD", "1000")),
        quick_sort_fraction_threshold=float(os.getenv("QUICK_SORT_FRACTION_THRESHOLD", "0.30")),
    )
