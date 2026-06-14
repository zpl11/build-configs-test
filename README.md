# my_py_utils

A core utility library for Python projects.

## Setup

### Create and activate virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Install for development

```bash
pip install -e .[dev]
```

### Install production only

```bash
pip install .
```

## Build

Install build tool and create distribution packages:

```bash
pip install build
python -m build
```

This creates:
- `dist/my_py_utils-0.1.0.tar.gz` (source distribution)
- `dist/my_py_utils-0.1.0-py3-none-any.whl` (wheel)

## Usage

```python
from my_py_utils.core import safe_deep_clone, is_valid_dict

data = {"key": "value"}
cloned = safe_deep_clone(data)
print(is_valid_dict(cloned))  # True
```

### CLI

```bash
py-util-cli
```
