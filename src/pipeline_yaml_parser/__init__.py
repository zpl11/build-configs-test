"""pipeline_yaml_parser - DevOps CI/CD pipeline configuration static analysis tool."""

from pipeline_yaml_parser.parser import load_pipeline_config, validate_stage_syntax

__all__ = ["load_pipeline_config", "validate_stage_syntax"]
__version__ = "0.1.0"
