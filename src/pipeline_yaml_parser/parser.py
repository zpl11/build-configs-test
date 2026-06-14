"""
Core parser module for DevOps CI/CD pipeline configuration static analysis.

Provides functions to load, parse, and validate pipeline YAML configuration files
used in continuous integration and deployment workflows.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_pipeline_config(path: Union[str, Path]) -> Dict[str, Any]:
    """Load and structure a CI/CD pipeline YAML configuration file.

    Parameters
    ----------
    path : str or Path
        Filesystem path to the pipeline YAML file.

    Returns
    -------
    dict
        A structured dictionary representing the parsed pipeline configuration.
        Top-level keys include ``stages``, ``variables``, and ``metadata``.

    Raises
    ------
    FileNotFoundError
        If *path* does not point to an existing file.
    yaml.YAMLError
        If the file contains invalid YAML syntax.
    ValueError
        If the parsed content is not a mapping at the top level.
    """
    file_path = Path(path)

    if not file_path.is_file():
        raise FileNotFoundError(f"Pipeline config not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as fh:
        raw: Any = yaml.safe_load(fh)

    if not isinstance(raw, dict):
        raise ValueError(
            f"Expected a YAML mapping at the top level, got {type(raw).__name__}"
        )

    # Normalise into a predictable structure
    config: Dict[str, Any] = {
        "metadata": {
            "source": str(file_path.resolve()),
            "pipeline_name": raw.get("name", file_path.stem),
        },
        "variables": _extract_variables(raw),
        "stages": _extract_stages(raw),
    }

    return config


def validate_stage_syntax(stage: Any) -> bool:
    """Validate whether a pipeline stage definition conforms to the expected schema.

    A valid stage must be a mapping that contains at least a ``name`` key (string)
    and optionally a ``steps`` key (list of mappings or strings).

    Parameters
    ----------
    stage : Any
        The stage object to validate (typically a dict parsed from YAML).

    Returns
    -------
    bool
        ``True`` if the stage is syntactically valid, ``False`` otherwise.
    """
    if not isinstance(stage, dict):
        return False

    # 'name' is required and must be a non-empty string
    name = stage.get("name")
    if not isinstance(name, str) or not name.strip():
        return False

    # 'steps', if present, must be a list
    steps = stage.get("steps")
    if steps is not None:
        if not isinstance(steps, list):
            return False
        for step in steps:
            if not isinstance(step, (dict, str)):
                return False

    return True


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> None:
    """Command-line entry-point for ``pipeline-lint-cli``.

    Performs a basic static lint of one or more pipeline YAML files, printing
    validation results to stdout and exiting with a non-zero code on failure.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="pipeline-lint-cli",
        description="Static analysis and linting for CI/CD pipeline YAML configs.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="One or more pipeline YAML files to lint.",
    )
    args = parser.parse_args(argv)

    exit_code = 0

    for file_path in args.files:
        print(f"[*] Linting: {file_path}")
        try:
            config = load_pipeline_config(file_path)
        except (FileNotFoundError, yaml.YAMLError, ValueError) as exc:
            print(f"  [ERROR] Failed to load: {exc}")
            exit_code = 1
            continue

        stages: List[Dict[str, Any]] = config.get("stages", [])
        all_valid = True

        for idx, stage in enumerate(stages):
            is_valid = validate_stage_syntax(stage)
            status = "OK" if is_valid else "INVALID"
            stage_name = stage.get("name", f"<index {idx}>") if isinstance(stage, dict) else f"<index {idx}>"
            print(f"  stage '{stage_name}': {status}")
            if not is_valid:
                all_valid = False

        if all_valid:
            print(f"  [PASS] All {len(stages)} stage(s) are valid.")
        else:
            print(f"  [FAIL] One or more stages failed validation.")
            exit_code = 1

    sys.exit(exit_code)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_variables(raw: Dict[str, Any]) -> Dict[str, str]:
    """Pull top-level variables / env block into a flat dict."""
    variables: Dict[str, str] = {}
    for key in ("variables", "env"):
        block = raw.get(key)
        if isinstance(block, dict):
            variables.update({str(k): str(v) for k, v in block.items()})
    return variables


def _extract_stages(raw: Dict[str, Any]) -> List[Any]:
    """Extract the stages list from common CI config layouts."""
    # GitLab / generic: top-level 'stages' key
    stages = raw.get("stages")
    if isinstance(stages, list):
        return stages

    # GitHub Actions: 'jobs' key
    jobs = raw.get("jobs")
    if isinstance(jobs, dict):
        return [
            {"name": job_name, **(job_def if isinstance(job_def, dict) else {})}
            for job_name, job_def in jobs.items()
        ]

    return []
