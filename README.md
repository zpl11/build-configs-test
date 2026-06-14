# my_py_utils

A lightweight Python utility library providing common helper functions.

## Project Structure

```
.
├── pyproject.toml            # Project metadata & build configuration (PEP 621)
├── README.md
└── src/
    └── my_py_utils/
        ├── __init__.py
        └── core.py           # Utility functions & CLI entry point
```

## Quick Start

### 1. Create and activate a virtual environment

```bash
# Create the venv
python -m venv .venv

# Activate (Linux / macOS)
source .venv/bin/activate

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (Windows cmd)
.venv\Scripts\activate.bat
```

### 2. Install in development mode (with dev dependencies)

```bash
pip install -e ".[dev]"
```

This installs the package in *editable* mode so that code changes take effect
immediately, and also pulls in the `dev` extras (`pytest`, etc.).

### 3. Run the CLI tool

After installation, the `py-util-cli` command is available in your terminal:

```bash
py-util-cli
```

### 4. Run tests

```bash
pytest
```

## Building Distribution Packages

To produce distributable `.whl` (wheel) and `.tar.gz` (sdist) archives:

```bash
# Install the build frontend
pip install build

# Build both wheel and sdist into the dist/ directory
python -m build
```

After the command completes you will find the artifacts under `dist/`:

```
dist/
├── my_py_utils-0.1.0-py3-none-any.whl
└── my_py_utils-0.1.0.tar.gz
```

You can then install the wheel directly:

```bash
pip install dist/my_py_utils-0.1.0-py3-none-any.whl
```

Or upload to PyPI using [twine](https://pypi.org/project/twine/):

```bash
pip install twine
twine upload dist/*
```

## License

MIT
