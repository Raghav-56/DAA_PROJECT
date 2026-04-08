from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def get_iso8601_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")



def error_response(error_code: str, message: str) -> dict[str, Any]:
    return {
        "status": "error",
        "error_code": error_code,
        "message": message,
        "timestamp": get_iso8601_timestamp(),
    }
