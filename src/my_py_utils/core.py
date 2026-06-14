import copy
from typing import Any, Dict
import requests


def safe_deep_clone(obj: Any) -> Any:
    """Safely deep clone an object using copy.deepcopy."""
    return copy.deepcopy(obj)


def is_valid_dict(obj: Any) -> bool:
    """Check if object is a valid non-empty dictionary."""
    return isinstance(obj, dict) and len(obj) > 0


def main():
    """CLI entry point."""
    print("my_py_utils CLI tool")
    test_data = {"key": "value", "nested": {"a": 1}}
    cloned = safe_deep_clone(test_data)
    print(f"Original: {test_data}")
    print(f"Cloned: {cloned}")
    print(f"Is valid dict: {is_valid_dict(test_data)}")
