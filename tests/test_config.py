from pathlib import Path

import pytest

from laytix.config import load_config, write_default_config


def test_load_config_resolves_relative_paths_from_config_file(tmp_path: Path) -> None:
    config_path = tmp_path / "project" / "laytix.yaml"
    config_path.parent.mkdir()
    config_path.write_text(
        """
project: Demo App
paths:
  baseline: screenshots/baseline
  actual: screenshots/actual
  report: reports/report.html
  diff_dir: reports/diffs
comparison:
  threshold: 0.05
  method: ssim
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.project == "Demo App"
    assert config.paths.baseline == config_path.parent / "screenshots" / "baseline"
    assert config.paths.actual == config_path.parent / "screenshots" / "actual"
    assert config.paths.report == config_path.parent / "reports" / "report.html"
    assert config.paths.diff_dir == config_path.parent / "reports" / "diffs"
    assert config.comparison.threshold == 0.05
    assert config.comparison.method == "ssim"


def test_load_config_rejects_invalid_threshold(tmp_path: Path) -> None:
    config_path = tmp_path / "laytix.yaml"
    config_path.write_text(
        """
comparison:
  threshold: 2
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="comparison.threshold"):
        load_config(config_path)


def test_load_config_rejects_invalid_comparison_method(tmp_path: Path) -> None:
    config_path = tmp_path / "laytix.yaml"
    config_path.write_text(
        """
comparison:
  method: magic
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="comparison.method"):
        load_config(config_path)


def test_load_config_requires_yaml_object(tmp_path: Path) -> None:
    config_path = tmp_path / "laytix.yaml"
    config_path.write_text("- not\n- an\n- object\n", encoding="utf-8")

    with pytest.raises(ValueError, match="YAML object"):
        load_config(config_path)


def test_write_default_config_creates_starter_file(tmp_path: Path) -> None:
    config_path = write_default_config(tmp_path / "laytix.yaml")

    assert config_path.exists()
    config = load_config(config_path)
    assert config.project == "Demo Android App"
    assert config.comparison.threshold == 0.02
    assert config.comparison.method == "pixel"


def test_write_default_config_does_not_overwrite_without_force(tmp_path: Path) -> None:
    config_path = tmp_path / "laytix.yaml"
    config_path.write_text("project: Existing\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="already exists"):
        write_default_config(config_path)

    assert config_path.read_text(encoding="utf-8") == "project: Existing\n"


def test_write_default_config_overwrites_with_force(tmp_path: Path) -> None:
    config_path = tmp_path / "laytix.yaml"
    config_path.write_text("project: Existing\n", encoding="utf-8")

    write_default_config(config_path, force=True)

    assert "Demo Android App" in config_path.read_text(encoding="utf-8")
