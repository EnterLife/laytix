from pathlib import Path

from PIL import Image
from typer.testing import CliRunner

from laytix.cli import app


def test_doctor_reports_python_packages() -> None:
    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "Python packages:" in result.output
    assert "scikit-image:" in result.output


def test_compare_command_uses_config_file(tmp_path: Path) -> None:
    baseline_dir = tmp_path / "baseline"
    actual_dir = tmp_path / "actual"
    report_path = tmp_path / "reports" / "report.html"
    config_path = tmp_path / "laytix.yaml"
    _make_image(baseline_dir / "login.png", (255, 255, 255))
    _make_image(actual_dir / "login.png", (255, 255, 255))
    config_path.write_text(
        """
project: CLI Config Test
paths:
  baseline: baseline
  actual: actual
  report: reports/report.html
comparison:
  threshold: 0.02
""",
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["compare", "--config", str(config_path)])

    assert result.exit_code == 0
    assert "Compared: 1" in result.output
    assert "Failed: 0" in result.output
    assert report_path.exists()
    assert "CLI Config Test" in report_path.read_text(encoding="utf-8")


def test_compare_command_cli_options_override_config(tmp_path: Path) -> None:
    baseline_dir = tmp_path / "baseline"
    actual_dir = tmp_path / "actual"
    report_path = tmp_path / "reports" / "override.html"
    config_path = tmp_path / "laytix.yaml"
    _make_image(baseline_dir / "login.png", (255, 255, 255))
    _make_image(actual_dir / "login.png", (0, 0, 0))
    config_path.write_text(
        """
project: CLI Config Test
paths:
  baseline: baseline
  actual: actual
  report: reports/report.html
comparison:
  threshold: 0.0
  method: ssim
""",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        [
            "compare",
            "--config",
            str(config_path),
            "--report",
            str(report_path),
            "--threshold",
            "1.0",
            "--method",
            "pixel",
        ],
    )

    assert result.exit_code == 0
    assert "Passed: 1" in result.output
    assert report_path.exists()


def test_compare_command_rejects_invalid_method(tmp_path: Path) -> None:
    baseline_dir = tmp_path / "baseline"
    actual_dir = tmp_path / "actual"
    report_path = tmp_path / "reports" / "report.html"
    _make_image(baseline_dir / "login.png", (255, 255, 255))
    _make_image(actual_dir / "login.png", (255, 255, 255))

    result = CliRunner().invoke(
        app,
        [
            "compare",
            "--baseline",
            str(baseline_dir),
            "--actual",
            str(actual_dir),
            "--report",
            str(report_path),
            "--method",
            "magic",
        ],
    )

    assert result.exit_code == 2
    assert "Comparison method" in result.output


def test_compare_command_requires_inputs_or_config() -> None:
    result = CliRunner().invoke(app, ["compare"])

    assert result.exit_code == 2
    assert "Missing required compare input" in result.output


def test_init_config_command_creates_config_file(tmp_path: Path) -> None:
    config_path = tmp_path / "laytix.yaml"

    result = CliRunner().invoke(app, ["init-config", "--output", str(config_path)])

    assert result.exit_code == 0
    assert "Laytix config created" in result.output
    assert "Demo Android App" in config_path.read_text(encoding="utf-8")


def test_init_config_command_requires_force_to_overwrite(tmp_path: Path) -> None:
    config_path = tmp_path / "laytix.yaml"
    config_path.write_text("project: Existing\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["init-config", "--output", str(config_path)])

    assert result.exit_code == 2
    assert "already exists" in result.output
    assert config_path.read_text(encoding="utf-8") == "project: Existing\n"


def test_init_config_command_overwrites_with_force(tmp_path: Path) -> None:
    config_path = tmp_path / "laytix.yaml"
    config_path.write_text("project: Existing\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["init-config", "--output", str(config_path), "--force"])

    assert result.exit_code == 0
    assert "Demo Android App" in config_path.read_text(encoding="utf-8")


def _make_image(path: Path, color: tuple[int, int, int], size: tuple[int, int] = (8, 8)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)
