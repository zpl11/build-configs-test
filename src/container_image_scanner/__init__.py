"""
container_image_scanner
=======================

A lightweight DevOps utility for auditing container image registries
and performing remote vulnerability scans against OCI/Docker artifacts.

Core Capabilities
-----------------
- Trigger remote vulnerability scans via HTTP API endpoints.
- Parse and filter vulnerability reports by severity level.
- Provide a CLI entry point for integration into CI/CD pipelines.

Usage Example
-------------
>>> from container_image_scanner.scanner import trigger_remote_scan, parse_vulnerability_report
>>> result = await trigger_remote_scan("https://registry.example.com", "my-app:latest")
>>> critical = parse_vulnerability_report(result, min_severity="HIGH")
"""

__version__ = "0.1.0"
__all__ = ["scanner"]
