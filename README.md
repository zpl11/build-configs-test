# devops_remote_executor

DevOps core engine for large-scale infrastructure remote configuration management and asymmetric concurrent command execution over encrypted SSH channels.

---

## Prerequisites

- Python **≥ 3.8**
- `pip` ≥ 23 (for PEP 621 support)

## Quick Start

### 1. Create and activate a local virtual environment

```bash
# Windows (cmd)
python -m venv .venv
.venv\Scripts\activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install the project in editable (development) mode

```bash
pip install -e .
```

This will also pull in all runtime dependencies (e.g. `paramiko`).

### 3. Install optional static-check dependencies

```bash
pip install -e ".[check]"
```

Then run type checking:

```bash
mypy src/
```

## Building distribution packages

Build both a **Wheel** (`.whl`) and a **source tarball** (`.tar.gz`) using the standard `build` front-end:

```bash
pip install build
python -m build
```

After the build completes, the artifacts will be available under `dist/`:

```
dist/
├── devops_remote_executor-0.1.0-py3-none-any.whl
└── devops_remote_executor-0.1.0.tar.gz
```

## CLI usage

Once installed, the `remote-exec-cli` command is available:

```bash
remote-exec-cli --host 10.0.0.1 --user admin --key ~/.ssh/id_rsa "uname -a"
```

Use `--help` for full options:

```bash
remote-exec-cli --help
```

## Project structure

```
.
├── pyproject.toml                          # PEP 517/621 project config
├── README.md
└── src/
    └── devops_remote_executor/
        ├── __init__.py
        └── ssh_client.py                   # SSH client & CLI entry-point
```

## License

MIT
