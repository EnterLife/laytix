"""Command-line interface for Laytix."""

from importlib.util import find_spec
import sys
from pathlib import Path
from typing import Annotated, cast

import typer

from laytix.adb import AdbError, capture_screenshot, find_adb, list_devices
from laytix.config import LaytixConfig, load_config, write_default_config
from laytix.compare import ComparisonMethod, SUPPORTED_COMPARISON_METHODS, compare_folders
from laytix.report import generate_html_report

app = typer.Typer(help="Laytix visual UI testing for Android apps.")

REQUIRED_PACKAGES = {
    "FastAPI": "fastapi",
    "NumPy": "numpy",
    "Pillow": "PIL",
    "PyYAML": "yaml",
    "scikit-image": "skimage",
    "Typer": "typer",
    "Uvicorn": "uvicorn",
}


@app.command()
def doctor() -> None:
    """Check the local Laytix environment."""
    typer.echo("Checking Laytix environment...")
    typer.echo(f"Python: {sys.version.split()[0]}")
    typer.echo("Python packages:")
    for package_name, import_name in REQUIRED_PACKAGES.items():
        status = "found" if find_spec(import_name) else "missing"
        typer.echo(f"- {package_name}: {status}")

    adb_path = find_adb()
    if adb_path:
        typer.echo(f"ADB: found at {adb_path}")
        try:
            devices = list_devices()
        except AdbError as error:
            typer.echo(f"ADB devices: {error}")
        else:
            typer.echo(f"Android devices: {len(devices)}")
    else:
        typer.echo("ADB: not found. Install Android Platform Tools and add adb to PATH.")


@app.command()
def capture(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output PNG file or folder for the captured screenshot."),
    ],
) -> None:
    """Capture a screenshot from a connected Android device or emulator."""
    try:
        screenshot_path = capture_screenshot(output)
    except AdbError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=2) from error

    typer.echo(f"Screenshot captured: {screenshot_path}")


@app.command("init-config")
def init_config(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Path for the generated Laytix YAML config."),
    ] = Path("laytix.yaml"),
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite the config file if it already exists."),
    ] = False,
) -> None:
    """Create a starter Laytix YAML config file."""
    try:
        config_path = write_default_config(output, force=force)
    except FileExistsError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=2) from error

    typer.echo(f"Laytix config created: {config_path}")


@app.command(name="compare")
def compare_command(
    baseline: Annotated[
        Path | None,
        typer.Option("--baseline", "-b", help="Folder with approved baseline images."),
    ] = None,
    actual: Annotated[
        Path | None,
        typer.Option("--actual", "-a", help="Folder with actual screenshot images."),
    ] = None,
    report: Annotated[
        Path | None,
        typer.Option("--report", "-r", help="Output HTML report path."),
    ] = None,
    threshold: Annotated[
        float | None,
        typer.Option("--threshold", "-t", help="Maximum allowed difference ratio."),
    ] = None,
    method: Annotated[
        str | None,
        typer.Option("--method", "-m", help="Comparison method: pixel or ssim."),
    ] = None,
    project: Annotated[
        str | None,
        typer.Option("--project", "-p", help="Project name shown in the report."),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Laytix YAML config file."),
    ] = None,
) -> None:
    """Compare screenshots and generate a report."""
    try:
        resolved = _resolve_compare_inputs(
            baseline=baseline,
            actual=actual,
            report=report,
            threshold=threshold,
            method=method,
            project=project,
            config_path=config,
        )
    except (FileNotFoundError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=2) from error

    baseline, actual, report, diff_dir, threshold, method, project = resolved
    typer.echo("Checking screenshots...")

    try:
        summary = compare_folders(
            baseline,
            actual,
            diff_dir,
            threshold=threshold,
            method=method,
            project_name=project,
        )
    except (FileNotFoundError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=2) from error

    generate_html_report(summary, report)

    typer.echo(f"Compared: {summary.total}")
    typer.echo(f"Passed: {summary.passed}")
    typer.echo(f"Failed: {summary.failed}")
    typer.echo(f"Report: {report}")

    if summary.has_failures:
        raise typer.Exit(code=1)


def _resolve_compare_inputs(
    *,
    baseline: Path | None,
    actual: Path | None,
    report: Path | None,
    threshold: float | None,
    method: str | None,
    project: str | None,
    config_path: Path | None,
) -> tuple[Path, Path, Path, Path, float, ComparisonMethod, str]:
    config = load_config(config_path) if config_path is not None else LaytixConfig()

    resolved_baseline = baseline or config.paths.baseline
    resolved_actual = actual or config.paths.actual
    resolved_report = report or config.paths.report
    resolved_diff_dir = config.paths.diff_dir or (resolved_report.parent / "diffs" if resolved_report else None)
    resolved_threshold = threshold if threshold is not None else config.comparison.threshold
    resolved_method = method or config.comparison.method
    resolved_project = project or config.project

    missing_options = []
    if resolved_baseline is None:
        missing_options.append("--baseline")
    if resolved_actual is None:
        missing_options.append("--actual")
    if resolved_report is None:
        missing_options.append("--report")

    if missing_options:
        missing = ", ".join(missing_options)
        raise ValueError(f"Missing required compare input: {missing}. Provide CLI options or --config.")

    if resolved_threshold < 0 or resolved_threshold > 1:
        raise ValueError("Threshold must be between 0 and 1.")

    if resolved_method not in SUPPORTED_COMPARISON_METHODS:
        supported = ", ".join(sorted(SUPPORTED_COMPARISON_METHODS))
        raise ValueError(f"Comparison method must be one of: {supported}.")

    return (
        resolved_baseline,
        resolved_actual,
        resolved_report,
        resolved_diff_dir,
        resolved_threshold,
        cast(ComparisonMethod, resolved_method),
        resolved_project,
    )


@app.command()
def web(
    host: Annotated[str, typer.Option("--host", help="Host for the local web interface.")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", "-p", help="Port for the local web interface.")] = 8000,
    reload: Annotated[bool, typer.Option("--reload", help="Reload the server on code changes.")] = False,
) -> None:
    """Start the local Laytix web interface."""
    try:
        import uvicorn
    except ImportError as error:
        typer.echo("Uvicorn is not installed. Run: python -m pip install -e \".[dev]\"", err=True)
        raise typer.Exit(code=2) from error

    typer.echo(f"Starting Laytix web interface: http://{host}:{port}")
    uvicorn.run("laytix.web:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
