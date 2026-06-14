"""Core utility functions for my_py_utils."""

import copy
import sys
from typing import Any, Dict

import requests  # noqa: F401 — declared as a runtime dependency


def safe_deep_clone(obj: Any) -> Any:
    """Return a deep copy of *obj*, safely handling objects that are not
    natively deep-copyable by falling back to a shallow copy.

    Parameters
    ----------
    obj : Any
        The object to clone.

    Returns
    -------
    Any
        A deep (or shallow, as fallback) copy of *obj*.
    """
    try:
        return copy.deepcopy(obj)
    except Exception:
        return copy.copy(obj)


def is_valid_dict(obj: Any) -> bool:
    """Check whether *obj* is a non-empty :class:`dict` whose keys are all
    strings.

    Parameters
    ----------
    obj : Any
        The object to check.

    Returns
    -------
    bool
        ``True`` if *obj* is a ``dict``, is not empty, and every key is a
        ``str``; ``False`` otherwise.
    """
    if not isinstance(obj, dict) or len(obj) == 0:
        return False
    return all(isinstance(k, str) for k in obj)


def main() -> None:
    """CLI entry point for ``py-util-cli``."""
    print("my_py_utils v0.1.0")
    print(f"Python {sys.version}")
    print()

    sample: Dict[str, int] = {"a": 1, "b": 2}
    cloned = safe_deep_clone(sample)
    print(f"Original : {sample}")
    print(f"Cloned   : {cloned}")
    print(f"Is valid dict (original) : {is_valid_dict(sample)}")
    print(f"Is valid dict (empty)    : {is_valid_dict({})}")


if __name__ == "__main__":
    main()
