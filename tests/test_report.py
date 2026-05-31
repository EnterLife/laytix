from pathlib import Path

from PIL import Image

from laytix.compare import compare_folders
from laytix.report import generate_html_report


def test_generate_html_report_includes_summary_and_relative_images(tmp_path: Path) -> None:
    baseline_dir = tmp_path / "baseline"
    actual_dir = tmp_path / "actual"
    report_path = tmp_path / "reports" / "report.html"
    _make_image(baseline_dir / "login.png", (255, 255, 255))
    _make_image(actual_dir / "login.png", (0, 0, 0))

    summary = compare_folders(
        baseline_dir,
        actual_dir,
        tmp_path / "reports" / "diffs",
        project_name="Demo Android App",
    )
    generated_path = generate_html_report(summary, report_path)

    html = generated_path.read_text(encoding="utf-8")
    assert "Demo Android App" in html
    assert "Total screens" in html
    assert "Failed" in html
    assert "../baseline/login.png" in html
    assert "../actual/login.png" in html
    assert "diffs/login.diff.png" in html


def _make_image(path: Path, color: tuple[int, int, int], size: tuple[int, int] = (8, 8)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)
