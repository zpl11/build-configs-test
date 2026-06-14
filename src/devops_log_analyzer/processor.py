"""
processor.py - Core log parsing and metric extraction engine.

Provides regex-based raw log line parsing and pydantic-backed
metric payload validation for DevOps production log streams.

Expected production log format::

    2024-01-15T10:23:45.123Z [INFO] service=api-gateway method=GET path=/api/v1/users status=200 duration=45ms bytes=1024 client_ip=192.168.1.100 request_id=req-abc-001
"""

import re
import sys
from typing import Any, Dict, List, Optional, Sequence

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Production log line pattern:
#   <ISO-8601 timestamp> [<LEVEL>] service=<svc> key=value ... key=value
_LOG_LINE_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+\-]\d{2}:\d{2}))"
    r"\s+\[(?P<level>[A-Z]+)\]"
    r"\s+service=(?P<service>[\w\-]+)"
    r"\s+(?P<fields>.*)$"
)

_KV_PAIR_RE = re.compile(r"([\w][\w\-]*)=(\S+)")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

VALID_HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARN", "WARNING", "ERROR", "FATAL", "CRITICAL"}


class MetricPayload(BaseModel):
    """Validated metric record extracted from a production log line.

    All numeric fields carry strict range constraints so that downstream
    metric aggregation pipelines never receive out-of-band values.
    """

    timestamp: str = Field(
        ..., description="ISO-8601 timestamp of the log event"
    )
    level: str = Field(..., description="Log severity level")
    service: str = Field(..., description="Originating service identifier")
    http_method: Optional[str] = Field(None, description="HTTP request method")
    path: Optional[str] = Field(None, description="Request URI path")
    status_code: Optional[int] = Field(
        None, ge=100, le=599, description="HTTP status code (100-599)"
    )
    duration_ms: Optional[float] = Field(
        None, ge=0, description="Request duration in milliseconds"
    )
    bytes_sent: Optional[int] = Field(
        None, ge=0, description="Response payload size in bytes"
    )
    client_ip: Optional[str] = Field(None, description="Client IP address")
    request_id: Optional[str] = Field(
        None, description="Unique request correlation ID"
    )

    @field_validator("level")
    @classmethod
    def _validate_level(cls, v: str) -> str:
        normalized = v.upper()
        if normalized not in VALID_LOG_LEVELS:
            raise ValueError(
                f"Unknown log level '{v}'. "
                f"Expected one of: {sorted(VALID_LOG_LEVELS)}"
            )
        return normalized

    @field_validator("http_method")
    @classmethod
    def _validate_http_method(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        normalized = v.upper()
        if normalized not in VALID_HTTP_METHODS:
            raise ValueError(
                f"Unknown HTTP method '{v}'. "
                f"Expected one of: {sorted(VALID_HTTP_METHODS)}"
            )
        return normalized

    @field_validator("status_code")
    @classmethod
    def _validate_status_code_semantics(cls, v: Optional[int]) -> Optional[int]:
        """Additional semantic guard-rail on top of pydantic ge/le constraints.

        The 100-599 range is already enforced by Field constraints, but this
        validator exists to centralise future business-rule extensions (e.g.
        rejecting deprecated status codes or flagging 3xx redirects).
        """
        if v is not None and 300 <= v < 400:
            # Redirects are semantically valid; pass-through for metric pipelines.
            pass
        return v


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_raw_log_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a single raw production log line into a structured dictionary.

    Applies the compiled regex ``_LOG_LINE_RE`` to decompose the line into
    its timestamp, severity level, originating service, and an arbitrary set
    of ``key=value`` fields commonly found in structured production logs.

    Args:
        line: Raw log line string from the ingestion stream.

    Returns:
        A dictionary with keys ``timestamp``, ``level``, ``service``, and
        ``fields`` (a flat dict of every ``key=value`` token found after the
        service tag).  Returns ``None`` if the line does not match the
        expected pattern, allowing callers to implement dead-letter routing.

    Example::

        >>> result = parse_raw_log_line(
        ...     "2024-01-15T10:23:45.123Z [INFO] service=api-gw method=GET status=200"
        ... )
        >>> result["fields"]["status"]
        '200'
    """
    line = line.strip()
    if not line:
        return None

    match = _LOG_LINE_RE.match(line)
    if not match:
        return None

    fields_raw: str = match.group("fields")
    fields: Dict[str, str] = dict(_KV_PAIR_RE.findall(fields_raw))

    return {
        "timestamp": match.group("timestamp"),
        "level": match.group("level"),
        "service": match.group("service"),
        "fields": fields,
    }


def validate_metric_payload(raw_parsed: Dict[str, Any]) -> MetricPayload:
    """Coerce and validate a parsed log dict into a :class:`MetricPayload`.

    Performs strict type coercion on duration strings (``"45ms"``, ``"1.2s"``),
    byte-count suffixes (``"1K"``, ``"2M"``), and raw numeric status codes,
    then delegates to pydantic for full schema validation.

    Args:
        raw_parsed: Dictionary as returned by :func:`parse_raw_log_line`.

    Returns:
        A fully validated :class:`MetricPayload` instance safe for
        downstream metric aggregation.

    Raises:
        pydantic.ValidationError: If any field fails constraint validation.
        KeyError: If required top-level keys (``timestamp``, ``level``,
            ``service``) are absent from *raw_parsed*.
    """
    fields: Dict[str, str] = raw_parsed.get("fields", {})

    # --- Coerce duration: "45ms" -> 45.0 | "1.2s" -> 1200.0 ----------------
    duration_raw = fields.get("duration")
    duration_ms: Optional[float] = None
    if duration_raw:
        if duration_raw.endswith("ms"):
            duration_ms = float(duration_raw[:-2])
        elif duration_raw.endswith("s"):
            duration_ms = float(duration_raw[:-1]) * 1000.0
        else:
            duration_ms = float(duration_raw)

    # --- Coerce byte count: "1024" | "1K" | "2M" ----------------------------
    bytes_raw = fields.get("bytes")
    bytes_sent: Optional[int] = None
    if bytes_raw:
        upper = bytes_raw.upper()
        if upper.endswith("K"):
            bytes_sent = int(float(bytes_raw[:-1]) * 1024)
        elif upper.endswith("M"):
            bytes_sent = int(float(bytes_raw[:-1]) * 1024 * 1024)
        else:
            bytes_sent = int(bytes_raw)

    # --- Coerce HTTP status code ---------------------------------------------
    status_raw = fields.get("status")
    status_code: Optional[int] = int(status_raw) if status_raw else None

    return MetricPayload(
        timestamp=raw_parsed["timestamp"],
        level=raw_parsed["level"],
        service=raw_parsed["service"],
        http_method=fields.get("method"),
        path=fields.get("path"),
        status_code=status_code,
        duration_ms=duration_ms,
        bytes_sent=bytes_sent,
        client_ip=fields.get("client_ip"),
        request_id=fields.get("request_id"),
    )


def process_log_stream(lines: Sequence[str]) -> List[MetricPayload]:
    """Process a sequence of raw log lines into validated metric payloads.

    Lines that fail regex matching are silently skipped with a stderr warning.
    Lines that parse successfully but fail pydantic validation are also skipped
    with a detailed stderr diagnostic.  This fail-open behaviour is intentional
    for production resilience — a single malformed line must never abort an
    entire log ingestion pipeline.

    Args:
        lines: Iterable of raw log line strings.

    Returns:
        List of validated :class:`MetricPayload` instances.
    """
    results: List[MetricPayload] = []
    for lineno, line in enumerate(lines, start=1):
        parsed = parse_raw_log_line(line)
        if parsed is None:
            print(
                f"[WARN] Line {lineno}: skipped (no pattern match)",
                file=sys.stderr,
            )
            continue
        try:
            metric = validate_metric_payload(parsed)
            results.append(metric)
        except Exception as exc:
            print(
                f"[WARN] Line {lineno}: validation failed - {exc}",
                file=sys.stderr,
            )
    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

_SAMPLE_LINES = [
    "2024-01-15T10:23:45.123Z [INFO] service=api-gateway method=GET path=/api/v1/users status=200 duration=45ms bytes=1024 client_ip=192.168.1.100 request_id=req-abc-001",
    "2024-01-15T10:23:46.456Z [ERROR] service=auth-service method=POST path=/auth/login status=401 duration=12ms bytes=256 client_ip=10.0.0.55 request_id=req-def-002",
    "2024-01-15T10:23:47.789Z [WARN] service=payment-svc method=POST path=/payments/charge status=502 duration=3200ms bytes=512 client_ip=172.16.0.9 request_id=req-ghi-003",
]


def main() -> None:
    """CLI entry point: read log lines from stdin (or demo) and emit JSON metrics.

    When invoked from a terminal without a piped stdin, runs a built-in demo
    with sample production log lines.  When stdin is piped (e.g. from
    ``tail -f`` or ``cat``), processes the incoming stream line-by-line.

    Output is a JSON array of validated metric objects written to stdout,
    suitable for ingestion by ``jq``, ``fluentd``, or any JSON-line consumer.
    """
    import json

    if sys.stdin.isatty():
        print(
            "devops_log_analyzer v0.1.0 - demo mode (no stdin pipe detected)\n",
            file=sys.stderr,
        )
        lines: Sequence[str] = _SAMPLE_LINES
    else:
        lines = sys.stdin.readlines()

    metrics = process_log_stream(lines)
    output = [m.model_dump() for m in metrics]
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
