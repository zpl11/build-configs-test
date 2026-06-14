# devops_sys_monitor

A lightweight DevOps toolkit for server metrics collection and system monitoring.

## Quick Start

### 1. Create and activate a virtual environment

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 2. Install the package in editable mode

```bash
pip install -e .
```

### 3. Install with lint tools (optional)

```bash
pip install -e ".[lint]"
```

### 4. Run the CLI

After installation, a `monitor-agent-cli` command is available:

```bash
monitor-agent-cli
```

This collects CPU, memory, and disk metrics and prints a JSON report to stdout.
If disk usage exceeds the default threshold (80%), a warning is printed to stderr.

## Build & Package

Install the build frontend:

```bash
pip install build
```

Build `.whl` and `.tar.gz` distribution archives:

```bash
python -m build
```

Artifacts will be generated in the `dist/` directory.

## Project Structure

```
pyproject.toml
src/
  devops_sys_monitor/
    __init__.py
    collector.py        # get_system_metrics, check_disk_alert, main
```
