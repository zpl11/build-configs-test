# devops_sys_monitor

A lightweight DevOps toolkit for server metrics collection and monitoring.

## Features

- **System metrics collection** - CPU, memory, swap, disk, and network stats in one call
- **Disk alert checking** - configurable threshold-based disk usage alerts
- **CLI tool** - one-command metric snapshot via `monitor-agent-cli`

## Prerequisites

- Python >= 3.8

## Quick Start

### 1. Create a virtual environment

```bash
python -m venv .venv

# Activate (Linux / macOS)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

### 2. Install the project (editable mode)

```bash
pip install -e .
```

### 3. Run the CLI tool

```bash
monitor-agent-cli
```

This will print a JSON snapshot of current system metrics and exit with code 1 if
any disk partition exceeds the default 85% threshold.

## Optional Dependencies

### Lint environment (flake8)

Install the lint extras for local code-quality checks:

```bash
pip install -e ".[lint]"
```

Then run:

```bash
flake8 src/
```

## Building & Packaging

### Install the build frontend

```bash
pip install build
```

### Build distribution artifacts

```bash
python -m build
```

This produces two artifacts under `dist/`:

| Artifact | Format | Purpose |
|---|---|---|
| `devops_sys_monitor-0.1.0.tar.gz` | Source distribution (sdist) | Reproducible source archive |
| `devops_sys_monitor-0.1.0-py3-none-any.whl` | Wheel (bdist_wheel) | Fast binary install |

### Upload to PyPI (optional)

```bash
pip install twine
twine upload dist/*
```

## Project Structure

```
.
├── pyproject.toml              # PEP 621 project metadata & build config
├── README.md
└── src/
    └── devops_sys_monitor/
        ├── __init__.py          # Package init, exposes __version__
        └── collector.py         # Metrics collector & CLI entry point
```

## API Reference

```python
from devops_sys_monitor.collector import get_system_metrics, check_disk_alert

# Collect all core metrics
metrics = get_system_metrics()

# Check disk alerts (default threshold: 85%)
result = check_disk_alert(threshold_percent=90.0, mountpoint="/")
if result["alert"]:
    print("Disk space critical!")
```

## License

MIT
