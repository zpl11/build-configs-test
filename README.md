# devops_log_analyzer

Infrastructure-grade toolkit for DevOps production log stream cleansing, unstructured text field parsing, and performance metric extraction.

## Quick Start

### 1. Create and activate a virtual environment

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (cmd)
.venv\Scripts\activate.bat
```

### 2. Install the package in development mode

```bash
pip install -e .
```

### 3. Install optional benchmark dependencies

To install the `bench` extras (includes `pytest-benchmark`):

```bash
pip install -e ".[bench]"
```

This keeps benchmark tooling isolated from the production dependency set.

### 4. Use the CLI

After installation the `log-parse-cli` command is available:

```bash
# Parse log lines from a file
cat /var/log/app/access.log | log-parse-cli

# Or on Windows
type access.log | log-parse-cli
```

## Building Distribution Packages

Build both `.whl` and `.tar.gz` artifacts using the standard `build` frontend:

```bash
# Install the build tool
pip install build

# Produce distributable archives in dist/
python -m build
```

The resulting files will be located in the `dist/` directory:

```
dist/
  devops_log_analyzer-0.1.0-py3-none-any.whl
  devops_log_analyzer-0.1.0.tar.gz
```

## Project Structure

```
├── pyproject.toml                  # PEP 621 project metadata & build config
├── README.md
└── src/
    └── devops_log_analyzer/
        ├── __init__.py
        └── processor.py           # Log parsing & metric validation
```
