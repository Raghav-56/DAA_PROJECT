from __future__ import annotations

import platform
import sys

import numpy as np
import pandas as pd
import psutil

from Src.common.utils import get_iso8601_timestamp



def capture_environment() -> dict[str, str | int | float]:
    vm = psutil.virtual_memory()
    return {
        "timestamp": get_iso8601_timestamp(),
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": psutil.cpu_count(logical=True) or 0,
        "memory_gb": round(vm.total / (1024**3), 2),
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
    }
