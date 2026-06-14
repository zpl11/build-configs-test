# infra_ping_checker

High-concurrency DevOps infrastructure network topology liveness detection and asset health walk-through toolkit.

## Quick Start

### 1. Create & activate a virtual environment

```bash
# Create
python -m venv .venv

# Activate (Linux / macOS)
source .venv/bin/activate

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1
```

### 2. Install in development mode (with test dependencies)

```bash
pip install -e ".[dev]"
```

This installs the package in editable mode along with `pytest` for testing.

### 3. Run the CLI

```bash
infra-ping-cli 8.8.8.8 1.1.1.1 192.168.1.1
```

### 4. Run tests

```bash
pytest
```

## Building Distribution Packages

Install the build frontend first:

```bash
pip install build
```

Then build both `.whl` and `.tar.gz` artifacts:

```bash
python -m build
```

The output will be placed in the `dist/` directory:

```
dist/
├── infra_ping_checker-0.1.0-py3-none-any.whl
└── infra_ping_checker-0.1.0.tar.gz
```

## Project Structure

```
.
├── pyproject.toml                   # PEP 621 project metadata & build config
├── README.md
└── src/
    └── infra_ping_checker/
        ├── __init__.py
        └── net_util.py              # Core network probing utilities
```
