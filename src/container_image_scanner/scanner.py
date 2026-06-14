"""Core scanning module for container image vulnerability auditing."""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional

import httpx


def trigger_remote_scan(
    registry_url: str,
    image: str,
    tag: str = "latest",
    *,
    timeout: float = 30.0,
    api_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Trigger a remote vulnerability scan on a container image via HTTP API.

    Args:
        registry_url: Base URL of the scanning service
            (e.g. "https://scanner.example.com").
        image: Full image name (e.g. "library/nginx").
        tag: Image tag to scan. Defaults to "latest".
        timeout: HTTP request timeout in seconds.
        api_token: Optional Bearer token for authentication.

    Returns:
        Parsed JSON response from the scanning service containing
        the scan report or a scan-job identifier.
    """
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"

    payload = {
        "image": image,
        "tag": tag,
    }

    with httpx.Client(timeout=timeout) as client:
        response = client.post(
            f"{registry_url.rstrip('/')}/api/v1/scan",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()


def parse_vulnerability_report(
    report: Dict[str, Any],
    min_severity: str = "MEDIUM",
) -> List[Dict[str, Any]]:
    """Filter a vulnerability report by minimum severity level.

    Accepts a scan report (as returned by the scanning service) and
    returns only those vulnerabilities whose severity is at or above
    the requested threshold.

    Severity ranking (low -> high):
        UNKNOWN < LOW < MEDIUM < HIGH < CRITICAL

    Args:
        report: Raw scan report dict; expected to contain a
            "vulnerabilities" key with a list of finding dicts,
            each having at least a "severity" field.
        min_severity: Minimum severity to include in results.

    Returns:
        Filtered list of vulnerability dicts.
    """
    severity_order = {
        "UNKNOWN": 0,
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
        "CRITICAL": 4,
    }

    threshold = severity_order.get(min_severity.upper(), 2)
    vulnerabilities: List[Dict[str, Any]] = report.get("vulnerabilities", [])

    return [
        vuln
        for vuln in vulnerabilities
        if severity_order.get(vuln.get("severity", "UNKNOWN").upper(), 0) >= threshold
    ]


def main() -> None:
    """CLI entry point for image-audit-cli.

    Usage:
        image-audit-cli <registry_url> <image> [tag] [--min-severity LEVEL]
    """
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(
            "Usage: image-audit-cli <registry_url> <image> [tag] "
            "[--min-severity LEVEL]\n\n"
            "Trigger a remote container image vulnerability scan and "
            "display filtered results.\n\n"
            "Severity levels: UNKNOWN, LOW, MEDIUM, HIGH, CRITICAL"
        )
        sys.exit(0)

    if len(args) < 2:
        print("Error: registry_url and image are required.", file=sys.stderr)
        sys.exit(1)

    registry_url = args[0]
    image = args[1]
    tag = "latest"
    min_severity = "MEDIUM"

    i = 2
    while i < len(args):
        if args[i] == "--min-severity" and i + 1 < len(args):
            min_severity = args[i + 1]
            i += 2
        elif not args[i].startswith("--"):
            tag = args[i]
            i += 1
        else:
            i += 1

    print(f"Scanning {image}:{tag} via {registry_url} ...")

    try:
        report = trigger_remote_scan(registry_url, image, tag)
    except httpx.HTTPStatusError as exc:
        print(f"Scan API error: {exc.response.status_code}", file=sys.stderr)
        sys.exit(1)
    except httpx.RequestError as exc:
        print(f"Connection error: {exc}", file=sys.stderr)
        sys.exit(1)

    filtered = parse_vulnerability_report(report, min_severity=min_severity)

    if not filtered:
        print(f"No vulnerabilities found at severity >= {min_severity}.")
    else:
        print(f"Found {len(filtered)} vulnerability(ies) "
              f"(>= {min_severity}):\n")
        print(json.dumps(filtered, indent=2, ensure_ascii=False))

    sys.exit(1 if filtered else 0)
