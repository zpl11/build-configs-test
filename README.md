# container_image_scanner

> A lightweight DevOps utility for auditing container image registries and performing remote vulnerability scans against OCI/Docker artifacts.

[![Python](https://img.shields.io/badge/python-≥%203.8-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [1. Create and Activate a Virtual Environment](#1-create-and-activate-a-virtual-environment)
  - [2. Install the Package](#2-install-the-package)
  - [3. Install Test Dependencies](#3-install-test-dependencies)
- [Usage](#usage)
  - [CLI Usage](#cli-usage)
  - [Programmatic Usage](#programmatic-usage)
- [Running Tests](#running-tests)
- [Building Distribution Artifacts](#building-distribution-artifacts)
- [Project Structure](#project-structure)

---

## Features

- **Remote Scan Triggering** — Send asynchronous HTTP requests to container registry scan APIs via `httpx`.
- **Severity-Based Filtering** — Filter vulnerability reports by minimum severity level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- **CLI Integration** — `image-audit-cli` console script for use in CI/CD pipelines.
- **Modern Packaging** — Built with PEP 517 / PEP 621 standards using `pyproject.toml`.
- **src-layout** — Clean separation between source code and project configuration.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | ≥ 3.8 |
| pip | ≥ 23.0 (recommended) |

---

## Getting Started

### 1. Create and Activate a Virtual Environment

A virtual environment provides physical isolation from system-wide Python packages, preventing dependency conflicts.

```bash
# Navigate to the project root
cd /path/to/ccrl014444

# Create a new virtual environment named ".venv"
python -m venv .venv

# ── Activate the virtual environment ──

# On Linux / macOS:
source .venv/bin/activate

# On Windows (cmd.exe):
.venv\Scripts\activate.bat

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Verify activation — the prompt should be prefixed with (.venv)
python --version
```

> **Tip:** Add `.venv/` to your `.gitignore` — virtual environments should never be committed to version control.

### 2. Install the Package

With the virtual environment activated, install the project in **editable (development) mode**:

```bash
# Upgrade pip and install the build frontend
python -m pip install --upgrade pip build

# Install in editable mode (development install)
pip install -e .
```

For production / non-editable installs:

```bash
pip install .
```

### 3. Install Test Dependencies

To install the optional `test` extra (which includes `pytest` and `pytest-cov`):

```bash
pip install -e ".[test]"
```

To install the full `dev` extra (adds linters, type checkers, and async test support):

```bash
pip install -e ".[dev]"
```

---

## Usage

### CLI Usage

After installation, the `image-audit-cli` command is available on your PATH:

```bash
image-audit-cli \
  --registry https://scan.example.com \
  --image my-app:v1.2 \
  --token sk-abc123 \
  --min-severity HIGH \
  --fixable-only \
  --json
```

**CLI Options:**

| Flag | Description | Default |
|---|---|---|
| `--registry` | Base URL of the scanning service API | *(required)* |
| `--image` | Image reference (`repository:tag`) | *(required)* |
| `--token` | Bearer token for API auth (or set `SCANNER_API_TOKEN`) | `None` |
| `--scan-endpoint` | API path for scan requests | `/api/v1/scan` |
| `--min-severity` | Minimum severity to report | `MEDIUM` |
| `--fixable-only` | Only show vulnerabilities with a known fix | `False` |
| `--json` | Output results as JSON | `False` |
| `--timeout` | HTTP request timeout in seconds | `60.0` |

**Exit Codes:**

| Code | Meaning |
|---|---|
| `0` | Scan completed; no critical vulnerabilities found |
| `1` | API error, network failure, or CRITICAL vulnerabilities detected |
| `2` | Invalid CLI arguments |

### Programmatic Usage

```python
import asyncio
from container_image_scanner.scanner import (
    trigger_remote_scan,
    parse_vulnerability_report,
)

async def audit():
    # Trigger the remote scan
    report = await trigger_remote_scan(
        registry_url="https://scan.example.com",
        image_ref="my-app:v1.2",
        api_token="sk-abc123",
    )

    # Filter for HIGH and CRITICAL vulnerabilities with available fixes
    critical = parse_vulnerability_report(
        report,
        min_severity="HIGH",
        include_fixable_only=True,
    )

    for vuln in critical:
        print(f"[{vuln['severity']}] {vuln['id']} in {vuln['package']}")

asyncio.run(audit())
```

---

## Running Tests

```bash
# Run all tests with verbose output
pytest

# Run tests with coverage reporting
pytest --cov=container_image_scanner --cov-report=term-missing

# Generate an HTML coverage report (open htmlcov/index.html in a browser)
pytest --cov=container_image_scanner --cov-report=html
```

---

## Building Distribution Artifacts

Use the official [`build`](https://pypa-build.readthedocs.io/) frontend (PEP 517 compliant) to produce clean, reproducible distribution packages:

```bash
# Ensure the build frontend is installed
pip install build

# Build both .whl (wheel) and .tar.gz (sdist) artifacts
python -m build

# The output will be placed in the "dist/" directory:
#   dist/
#   ├── container_image_scanner-0.1.0-py3-none-any.whl
#   └── container_image_scanner-0.1.0.tar.gz
```

### Build a Specific Format

```bash
# Build only the wheel (.whl)
python -m build --wheel

# Build only the source distribution (.tar.gz)
python -m build --sdist
```

### Install from Built Artifacts

```bash
# Install directly from the wheel
pip install dist/container_image_scanner-0.1.0-py3-none-any.whl

# Or install from the source distribution
pip install dist/container_image_scanner-0.1.0.tar.gz
```

### Verify the Package

```bash
# Check package metadata
pip show container_image_scanner

# Verify the CLI entry point is registered
which image-audit-cli        # Linux/macOS
where image-audit-cli        # Windows

# Run the CLI help
image-audit-cli --help
```

---

## Project Structure

```
ccrl014444/
├── pyproject.toml                        # PEP 621 project metadata & build config
├── README.md                             # This file
├── .gitignore                            # Version control ignore patterns
├── src/
│   └── container_image_scanner/
│       ├── __init__.py                   # Package initialization & version
│       └── scanner.py                    # Core scanning logic & CLI entry point
└── tests/                                # (Create this directory for test files)
    └── ...
```

### Key Design Decisions

| Decision | Rationale |
|---|---|
| **src-layout** | Prevents accidental imports of uninstalled code; standard for modern Python packages |
| **PEP 621 metadata** | Declarative, tool-agnostic metadata in `pyproject.toml` |
| **setuptools backend** | Widely supported, stable build backend with broad ecosystem compatibility |
| **httpx (async)** | Modern HTTP client with native async support, HTTP/2, and a requests-compatible API |
| **argparse CLI** | Zero extra dependencies for CLI parsing; batteries-included from stdlib |

---

## License

This project is licensed under the MIT License.
