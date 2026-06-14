# DevOps Remote Executor

A DevOps core engine for large-scale infrastructure remote configuration management and asymmetric concurrent command execution.

## Prerequisites

- Python >= 3.8
- pip >= 21.0 (with PEP 517 support)

## Quick Start

### 1. Create and activate a virtual environment

```bash
# Create the virtual environment
python -m venv .venv

# Activate (Linux / macOS)
source .venv/bin/activate

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (Windows CMD)
.venv\Scripts\activate.bat
```

### 2. Install the project in editable mode

```bash
pip install -e .
```

This will install the `devops_remote_executor` package along with its runtime
dependency (`paramiko`) and register the `remote-exec-cli` console command.

### 3. Install optional static type-checking dependencies

```bash
pip install -e ".[check]"
```

This adds `mypy` for static type analysis. Run it with:

```bash
mypy src/
```

### 4. Verify the installation

```bash
remote-exec-cli --help
```

## Building Distribution Packages

Use the standard `build` front-end (PEP 517) to produce both a Wheel (`.whl`)
and a source distribution (`.tar.gz`):

```bash
# Install the build tool
pip install build

# Build wheel and sdist into the dist/ directory
python -m build
```

After a successful build, the artifacts will be located in `dist/`:

```
dist/
  devops_remote_executor-0.1.0-py3-none-any.whl
  devops_remote_executor-0.1.0.tar.gz
```

## Usage

```bash
# Execute a command on a remote host
remote-exec-cli myhost.example.com "uname -a" -u admin -k ~/.ssh/id_rsa

# Specify a custom port and timeout
remote-exec-cli 192.168.1.100 "df -h" -p 2222 -t 30 -u root
```

## Project Structure

```
.
├── pyproject.toml                          # Build system and project metadata
├── README.md
└── src/
    └── devops_remote_executor/
        ├── __init__.py                     # Package version
        └── ssh_client.py                   # SSH connection and command execution
```
