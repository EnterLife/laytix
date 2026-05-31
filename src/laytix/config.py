"""Configuration loading for Laytix."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

import yaml

ComparisonMethod = Literal["pixel", "ssim"]
SUPPORTED_COMPARISON_METHODS = {"pixel", "ssim"}

DEFAULT_CONFIG_TEMPLATE = """project: Demo Android App

paths:
  baseline: examples/baseline
  actual: examples/actual
  report: examples/reports/report.html
  diff_dir: examples/reports/diffs

comparison:
  threshold: 0.02
  method: pixel
"""


@dataclass(frozen=True)
class ComparisonConfig:
    """Comparison settings loaded from a Laytix config file."""

    threshold: float = 0.02
    method: ComparisonMethod = "pixel"


@dataclass(frozen=True)
class PathConfig:
    """Input and output paths loaded from a Laytix config file."""

    baseline: Path | None = None
    actual: Path | None = None
    report: Path | None = None
    diff_dir: Path | None = None


@dataclass(frozen=True)
class LaytixConfig:
    """Top-level Laytix configuration."""

    project: str = "Laytix project"
    paths: PathConfig = PathConfig()
    comparison: ComparisonConfig = ComparisonConfig()


def load_config(config_path: Path | str) -> LaytixConfig:
    """Load a Laytix YAML config file."""

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file does not exist: {path}")

    raw_config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw_config, dict):
        raise ValueError("Config file must contain a YAML object.")

    config_dir = path.parent
    return LaytixConfig(
        project=_read_string(raw_config, "project", default="Laytix project"),
        paths=_read_paths(raw_config.get("paths", {}), config_dir),
        comparison=_read_comparison(raw_config.get("comparison", {})),
    )


def write_default_config(output_path: Path | str, *, force: bool = False) -> Path:
    """Write a starter Laytix YAML config file."""

    path = Path(output_path)
    if path.exists() and not force:
        raise FileExistsError(f"Config file already exists: {path}. Use --force to overwrite it.")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DEFAULT_CONFIG_TEMPLATE, encoding="utf-8")
    return path


def _read_paths(raw_paths: Any, config_dir: Path) -> PathConfig:
    if raw_paths is None:
        raw_paths = {}

    if not isinstance(raw_paths, dict):
        raise ValueError("Config field 'paths' must be a YAML object.")

    return PathConfig(
        baseline=_read_optional_path(raw_paths, "baseline", config_dir),
        actual=_read_optional_path(raw_paths, "actual", config_dir),
        report=_read_optional_path(raw_paths, "report", config_dir),
        diff_dir=_read_optional_path(raw_paths, "diff_dir", config_dir),
    )


def _read_comparison(raw_comparison: Any) -> ComparisonConfig:
    if raw_comparison is None:
        raw_comparison = {}

    if not isinstance(raw_comparison, dict):
        raise ValueError("Config field 'comparison' must be a YAML object.")

    threshold = raw_comparison.get("threshold", 0.02)
    if not isinstance(threshold, int | float):
        raise ValueError("Config field 'comparison.threshold' must be a number.")

    threshold = float(threshold)
    if threshold < 0 or threshold > 1:
        raise ValueError("Config field 'comparison.threshold' must be between 0 and 1.")

    method = raw_comparison.get("method", "pixel")
    if not isinstance(method, str):
        raise ValueError("Config field 'comparison.method' must be a string.")

    if method not in SUPPORTED_COMPARISON_METHODS:
        supported = ", ".join(sorted(SUPPORTED_COMPARISON_METHODS))
        raise ValueError(f"Config field 'comparison.method' must be one of: {supported}.")

    return ComparisonConfig(threshold=threshold, method=cast(ComparisonMethod, method))


def _read_string(raw_config: dict[str, Any], key: str, *, default: str) -> str:
    value = raw_config.get(key, default)
    if not isinstance(value, str):
        raise ValueError(f"Config field '{key}' must be a string.")
    return value


def _read_optional_path(raw_config: dict[str, Any], key: str, config_dir: Path) -> Path | None:
    value = raw_config.get(key)
    if value is None:
        return None

    if not isinstance(value, str):
        raise ValueError(f"Config field 'paths.{key}' must be a string.")

    path = Path(value)
    if path.is_absolute():
        return path

    return config_dir / path
