"""
scanner.py
==========

Core module for triggering remote container image vulnerability scans
and parsing the resulting reports.

This module provides:
  - ``trigger_remote_scan``: Async HTTP call to a registry's scan API.
  - ``parse_vulnerability_report``: Severity-based filtering of scan results.
  - ``main``: CLI entry point for ``image-audit-cli``.

Dependencies
------------
- httpx  – modern async-capable HTTP client (required).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any, Dict, List, Optional

import httpx

# ─────────────────────────────────────────────────────────────────────────────
# Severity level definitions (ordered from least to most severe)
# ─────────────────────────────────────────────────────────────────────────────
SEVERITY_ORDER: List[str] = ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]


def _severity_rank(level: str) -> int:
    """Return a numeric rank for a severity string (higher = more severe).

    Parameters
    ----------
    level : str
        Severity label (case-insensitive). One of: NONE, LOW, MEDIUM,
        HIGH, CRITICAL.

    Returns
    -------
    int
        Numeric rank; unknown labels default to 0 (equivalent to NONE).
    """
    try:
        return SEVERITY_ORDER.index(level.upper())
    except ValueError:
        return 0


# ─────────────────────────────────────────────────────────────────────────────
# Remote scan trigger
# ─────────────────────────────────────────────────────────────────────────────
async def trigger_remote_scan(
    registry_url: str,
    image_ref: str,
    *,
    api_token: Optional[str] = None,
    scan_endpoint: str = "/api/v1/scan",
    timeout: float = 60.0,
) -> Dict[str, Any]:
    """Trigger a remote vulnerability scan for a container image via HTTP.

    Sends an asynchronous POST request to the registry's scan API endpoint
    to initiate a vulnerability assessment of the specified image.

    Parameters
    ----------
    registry_url : str
        Base URL of the container registry or scanning service
        (e.g. ``"https://registry.example.com"``).
    image_ref : str
        Image reference in ``repository:tag`` format
        (e.g. ``"my-app:latest"`` or ``"library/nginx:1.25"``).
    api_token : str, optional
        Bearer token for authenticating against the scan API.
        If ``None``, the request is sent without an Authorization header.
    scan_endpoint : str, optional
        API path relative to *registry_url* that accepts scan requests.
        Defaults to ``"/api/v1/scan"``.
    timeout : float, optional
        Maximum time in seconds to wait for the HTTP response.
        Defaults to ``60.0``.

    Returns
    -------
    dict
        Parsed JSON response body from the scanning service.  Expected
        keys include ``"scan_id"``, ``"status"``, and ``"vulnerabilities"``.

    Raises
    ------
    httpx.HTTPStatusError
        If the API responds with a 4xx or 5xx status code.
    httpx.RequestError
        If a transport-level error occurs (DNS failure, connection refused, …).

    Examples
    --------
    >>> import asyncio
    >>> result = asyncio.run(
    ...     trigger_remote_scan(
    ...         "https://scan.example.com",
    ...         "my-app:v1.2",
    ...         api_token="sk-abc123",
    ...     )
    ... )
    >>> result["scan_id"]
    'scan-20260614-abcdef'
    """
    url = registry_url.rstrip("/") + scan_endpoint

    headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": f"container_image_scanner/0.1.0",
    }
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"

    payload: Dict[str, Any] = {
        "image": image_ref,
        "scan_type": "vulnerability",
        "options": {
            "include_fixable_only": False,
            "depth": "full",
        },
    }

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(timeout, connect=10.0),
        follow_redirects=True,
    ) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()


# ─────────────────────────────────────────────────────────────────────────────
# Vulnerability report parsing and filtering
# ─────────────────────────────────────────────────────────────────────────────
def parse_vulnerability_report(
    report: Dict[str, Any],
    *,
    min_severity: str = "MEDIUM",
    include_fixable_only: bool = False,
) -> List[Dict[str, Any]]:
    """Parse a scan report and return vulnerabilities meeting the severity threshold.

    Parameters
    ----------
    report : dict
        Raw scan report as returned by :func:`trigger_remote_scan`.  Must
        contain a ``"vulnerabilities"`` key whose value is a list of dicts,
        each with at least ``"id"``, ``"severity"``, and ``"package"`` keys.
    min_severity : str, optional
        Minimum severity level to include in the filtered output.
        Accepted values (case-insensitive): ``NONE``, ``LOW``, ``MEDIUM``,
        ``HIGH``, ``CRITICAL``.  Defaults to ``"MEDIUM"``.
    include_fixable_only : bool, optional
        When ``True``, only vulnerabilities that have a known fix version
        (``"fixed_in"`` key present and non-empty) are returned.

    Returns
    -------
    list[dict]
        Filtered list of vulnerability entries.  Each entry is a dict
        with the original keys from the report plus an added
        ``"severity_rank"`` integer for programmatic sorting.

    Examples
    --------
    >>> report = {
    ...     "scan_id": "scan-001",
    ...     "vulnerabilities": [
    ...         {"id": "CVE-2024-1234", "severity": "LOW",     "package": "libx",  "fixed_in": ""},
    ...         {"id": "CVE-2024-5678", "severity": "HIGH",    "package": "openssl","fixed_in": "1.1.1w"},
    ...         {"id": "CVE-2024-9999", "severity": "CRITICAL","package": "glibc",  "fixed_in": "2.38-3"},
    ...     ],
    ... }
    >>> critical_and_high = parse_vulnerability_report(report, min_severity="HIGH")
    >>> [v["id"] for v in critical_and_high]
    ['CVE-2024-5678', 'CVE-2024-9999']
    """
    threshold_rank = _severity_rank(min_severity)
    vulnerabilities: List[Dict[str, Any]] = report.get("vulnerabilities", [])
    filtered: List[Dict[str, Any]] = []

    for vuln in vulnerabilities:
        severity: str = vuln.get("severity", "NONE")
        rank = _severity_rank(severity)

        # Skip entries below the minimum severity threshold
        if rank < threshold_rank:
            continue

        # Optionally restrict to vulnerabilities with a known fix
        if include_fixable_only and not vuln.get("fixed_in"):
            continue

        entry = dict(vuln)
        entry["severity_rank"] = rank
        filtered.append(entry)

    # Sort by descending severity (most critical first), then by CVE ID
    filtered.sort(key=lambda v: (-v["severity_rank"], v.get("id", "")))
    return filtered


# ─────────────────────────────────────────────────────────────────────────────
# Report formatting helpers
# ─────────────────────────────────────────────────────────────────────────────
def _format_vuln_table(vulns: List[Dict[str, Any]]) -> str:
    """Return a plain-text table summarising filtered vulnerabilities."""
    if not vulns:
        return "[OK] No vulnerabilities found matching the specified criteria."

    header = f"{'CVE ID':<22} {'Severity':<10} {'Package':<20} {'Fixed In':<15}"
    sep = "-" * len(header)
    rows = [
        f"{v.get('id', 'N/A'):<22} "
        f"{v.get('severity', 'N/A'):<10} "
        f"{v.get('package', 'N/A'):<20} "
        f"{v.get('fixed_in', '—'):<15}"
        for v in vulns
    ]
    return "\n".join([header, sep, *rows])


def _print_summary(scan_id: str, total: int, filtered_count: int, min_severity: str) -> None:
    """Print a scan summary header to stdout."""
    print(f"\n{'=' * 67}")
    print(f"  Container Image Vulnerability Audit Report")
    print(f"{'=' * 67}")
    print(f"  Scan ID        : {scan_id}")
    print(f"  Total vulns    : {total}")
    print(f"  Filtered (>= {min_severity.upper()}): {filtered_count}")
    print(f"{'=' * 67}\n")


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────
def _build_parser() -> argparse.ArgumentParser:
    """Construct the argparse parser for ``image-audit-cli``."""
    parser = argparse.ArgumentParser(
        prog="image-audit-cli",
        description=(
            "Audit container images for known vulnerabilities by triggering "
            "remote scans against a registry or scanning service API."
        ),
        epilog=(
            "Example:\n"
            "  image-audit-cli --registry https://scan.example.com "
            "--image my-app:latest --min-severity HIGH --token sk-abc123\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--registry",
        required=True,
        help="Base URL of the container registry / scanning service.",
    )
    parser.add_argument(
        "--image",
        required=True,
        help="Image reference in 'repository:tag' format.",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Bearer token for API authentication (or set SCANNER_API_TOKEN env var).",
    )
    parser.add_argument(
        "--scan-endpoint",
        default="/api/v1/scan",
        help="API path for triggering scans (default: /api/v1/scan).",
    )
    parser.add_argument(
        "--min-severity",
        default="MEDIUM",
        choices=[s.lower() for s in SEVERITY_ORDER],
        help="Minimum severity level to report (default: MEDIUM).",
    )
    parser.add_argument(
        "--fixable-only",
        action="store_true",
        help="Only report vulnerabilities with a known fix version.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output results as JSON instead of a human-readable table.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="HTTP request timeout in seconds (default: 60).",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point invoked by the ``image-audit-cli`` console script.

    Parameters
    ----------
    argv : list[str], optional
        Command-line arguments.  Defaults to ``sys.argv[1:]`` when ``None``.

    Returns
    -------
    int
        Exit code: ``0`` on success, ``1`` on API/network error, ``2`` on
        argument parsing error.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Resolve token from argument or environment variable
    import os

    api_token = args.token or os.environ.get("SCANNER_API_TOKEN")

    async def _run() -> int:
        try:
            print(f"[*] Triggering remote scan for '{args.image}' "
                  f"on {args.registry} ...")
            report = await trigger_remote_scan(
                registry_url=args.registry,
                image_ref=args.image,
                api_token=api_token,
                scan_endpoint=args.scan_endpoint,
                timeout=args.timeout,
            )
        except httpx.HTTPStatusError as exc:
            print(
                f"[ERROR] API returned HTTP {exc.response.status_code}: "
                f"{exc.response.text}",
                file=sys.stderr,
            )
            return 1
        except httpx.RequestError as exc:
            print(f"[ERROR] Network error: {exc}", file=sys.stderr)
            return 1

        scan_id: str = report.get("scan_id", "unknown")
        all_vulns: List[Dict[str, Any]] = report.get("vulnerabilities", [])

        filtered = parse_vulnerability_report(
            report,
            min_severity=args.min_severity,
            include_fixable_only=args.fixable_only,
        )

        if args.output_json:
            output = {
                "scan_id": scan_id,
                "min_severity": args.min_severity.upper(),
                "total_vulnerabilities": len(all_vulns),
                "filtered_count": len(filtered),
                "vulnerabilities": filtered,
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            _print_summary(scan_id, len(all_vulns), len(filtered), args.min_severity)
            print(_format_vuln_table(filtered))

        # Exit with code 1 if any CRITICAL vulnerabilities were found
        if any(v.get("severity", "").upper() == "CRITICAL" for v in filtered):
            print("\n[!] CRITICAL vulnerabilities detected — failing audit.", file=sys.stderr)
            return 1

        return 0

    return asyncio.run(_run())


# ─────────────────────────────────────────────────────────────────────────────
# Allow direct execution: python -m container_image_scanner.scanner
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sys.exit(main())
