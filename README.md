# Container Image Scanner

A lightweight DevOps infrastructure tool for container image registry security auditing and remote vulnerability scanning.

## Features

- Trigger remote vulnerability scans on container images via HTTP API
- Filter scan results by severity level (UNKNOWN / LOW / MEDIUM / HIGH / CRITICAL)
- CLI tool `image-audit-cli` for quick terminal-based auditing

## Project Structure

```
.
├── pyproject.toml
├── README.md
└── src/
    └── container_image_scanner/
        ├── __init__.py
        └── scanner.py
```

## Quick Start

### 1. Create and activate a virtual environment

Use Python's built-in `venv` module to create an isolated environment, preventing dependency conflicts with the system Python installation.

```bash
# Create venv
python -m venv .venv

# Activate (Linux / macOS)
source .venv/bin/activate

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (Windows CMD)
.venv\Scripts\activate.bat
```

### 2. Install the package in development mode

Install the project as an editable package so that code changes take effect immediately without reinstallation.

```bash
# Install with production dependencies
pip install -e .

# Install with test dependencies
pip install -e ".[test]"
```

### 3. Run the CLI

After installation, the `image-audit-cli` command is available in your terminal:

```bash
# Show help
image-audit-cli --help

# Run a scan
image-audit-cli https://scanner.example.com library/nginx latest --min-severity HIGH
```

## Building Distribution Packages

Use the standard `build` module (PEP 517) to produce clean `.whl` and `.tar.gz` distribution artifacts.

```bash
# Install the build frontend
pip install build

# Build wheel and sdist into the dist/ directory
python -m build
```

After building, the `dist/` directory will contain:

```
dist/
├── container_image_scanner-0.1.0-py3-none-any.whl
└── container_image_scanner-0.1.0.tar.gz
```

These artifacts can be uploaded to PyPI or a private registry using `twine`:

```bash
pip install twine
twine upload dist/*
```

## Running Tests

```bash
# Run tests with coverage
pytest --cov=container_image_scanner
```

## License

MIT
