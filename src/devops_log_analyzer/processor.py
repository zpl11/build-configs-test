"""Core log processing module.

Provides regex-based raw log parsing and pydantic-powered metric validation
for DevOps production log streams.
"""

from __future__ import annotations

import re
import sys
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

# ---------------------------------------------------------------------------
# Common log line pattern
# Matches lines like:
#   2024-06-01T12:34:56.789Z INFO  [service-name] GET /api/health 200 12ms
#   2024-06-01 12:34:56 ERROR [worker-3] POST /api/data 500 340ms
# ---------------------------------------------------------------------------
_LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)\s+"
    r"(?P<level>DEBUG|INFO|WARN(?:ING)?|ERROR|FATAL|CRITICAL)\s+"
    r"(?:\[(?P<service>[^\]]+)\]\s+)?"
    r"(?:(?P<method>GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+)?"
    r"(?P<path>/\S+)?\s*"
    r"(?P<status_code>\d{3})?\s*"
    r"(?P<duration_ms>\d+)?(?:ms)?"
)


def parse_raw_log_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a single raw log line using regex pattern matching.

    Parameters
    ----------
    line:
        A raw log line string from a production log stream.

    Returns
    -------
    A dictionary containing extracted fields (timestamp, level, service,
    method, path, status_code, duration_ms) or ``None`` if the line does
    not match the expected pattern.
    """
    line = line.strip()
    if not line:
        return None

    match = _LOG_PATTERN.match(line)
    if not match:
        return None

    data = match.groupdict()

    if data.get("status_code") is not None:
        data["status_code"] = int(data["status_code"])
    if data.get("duration_ms") is not None:
        data["duration_ms"] = int(data["duration_ms"])

    return data


# ---------------------------------------------------------------------------
# Pydantic models for metric payload validation
# ---------------------------------------------------------------------------

class MetricPayload(BaseModel):
    """Schema for an HTTP performance metric data point.

    Enforces strict structural compliance for downstream ingestion
    (e.g. Prometheus push-gateway, OpenTelemetry collector).
    """

    service: str = Field(..., min_length=1, description="Originating service name")
    method: str = Field(..., description="HTTP method")
    path: str = Field(..., min_length=1, description="Request path")
    status_code: int = Field(..., ge=100, le=599, description="HTTP status code")
    duration_ms: int = Field(..., ge=0, description="Request duration in milliseconds")
    tags: Optional[Dict[str, str]] = Field(default=None, description="Optional key-value tags")

    @validator("method")
    def _validate_method(cls, v: str) -> str:  # noqa: N805
        allowed = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"Invalid HTTP method: {v!r}")
        return upper


def validate_metric_payload(data: Dict[str, Any]) -> MetricPayload:
    """Validate and normalise a raw metric dictionary.

    Parameters
    ----------
    data:
        Raw dictionary typically produced by :func:`parse_raw_log_line`.

    Returns
    -------
    A fully-validated :class:`MetricPayload` instance.

    Raises
    ------
    pydantic.ValidationError
        When the payload fails structural or value compliance checks.
    """
    return MetricPayload(**data)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Read log lines from stdin, parse each line, and print extracted fields."""
    parsed = 0
    errors = 0

    for line in sys.stdin:
        result = parse_raw_log_line(line)
        if result is None:
            errors += 1
            continue

        parsed += 1
        parts: List[str] = []
        for key in ("timestamp", "level", "service", "method", "path", "status_code", "duration_ms"):
            value = result.get(key)
            if value is not None:
                parts.append(f"{key}={value}")
        print(" | ".join(parts))

    print(f"\n--- Summary: {parsed} parsed, {errors} skipped ---", file=sys.stderr)


if __name__ == "__main__":
    main()
