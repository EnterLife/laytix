from pathlib import Path

import pytest
from PIL import Image

from laytix.compare import compare_folders, compare_image_pair


def test_identical_images_pass(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.png"
    actual = tmp_path / "actual.png"
    diff = tmp_path / "diff.png"
    _make_image(baseline, (255, 255, 255))
    _make_image(actual, (255, 255, 255))

    result = compare_image_pair(baseline, actual, diff, threshold=0.0)

    assert result.passed is True
    assert result.difference_ratio == 0.0
    assert diff.exists()


def test_different_images_fail_when_threshold_is_exceeded(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.png"
    actual = tmp_path / "actual.png"
    diff = tmp_path / "diff.png"
    _make_image(baseline, (255, 255, 255))
    _make_image(actual, (0, 0, 0))

    result = compare_image_pair(baseline, actual, diff, threshold=0.02)

    assert result.passed is False
    assert result.difference_ratio == 1.0
    assert result.reason == "Difference ratio exceeds threshold."
    assert diff.exists()


def test_ssim_comparison_detects_visual_difference(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.png"
    actual = tmp_path / "actual.png"
    diff = tmp_path / "diff.png"
    _make_image(baseline, (255, 255, 255), size=(20, 20))
    _make_image(actual, (0, 0, 0), size=(20, 20))

    result = compare_image_pair(baseline, actual, diff, threshold=0.02, method="ssim")

    assert result.passed is False
    assert result.difference_ratio > 0.02
    assert diff.exists()


def test_ssim_comparison_passes_identical_images(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.png"
    actual = tmp_path / "actual.png"
    diff = tmp_path / "diff.png"
    _make_image(baseline, (255, 255, 255), size=(20, 20))
    _make_image(actual, (255, 255, 255), size=(20, 20))

    result = compare_image_pair(baseline, actual, diff, threshold=0.0, method="ssim")

    assert result.passed is True
    assert result.difference_ratio == pytest.approx(0.0)
    assert diff.exists()


def test_unknown_comparison_method_is_rejected(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.png"
    actual = tmp_path / "actual.png"
    _make_image(baseline, (255, 255, 255))
    _make_image(actual, (255, 255, 255))

    with pytest.raises(ValueError, match="Comparison method"):
        compare_image_pair(baseline, actual, tmp_path / "diff.png", method="unknown")  # type: ignore[arg-type]


def test_partial_difference_can_pass_under_threshold(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.png"
    actual = tmp_path / "actual.png"
    diff = tmp_path / "diff.png"
    _make_image(baseline, (255, 255, 255), size=(10, 10))
    _make_image(actual, (255, 255, 255), size=(10, 10))

    image = Image.open(actual)
    image.putpixel((0, 0), (0, 0, 0))
    image.save(actual)

    result = compare_image_pair(baseline, actual, diff, threshold=0.02)

    assert result.passed is True
    assert result.difference_ratio == pytest.approx(0.01)


def test_size_mismatch_fails(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.png"
    actual = tmp_path / "actual.png"
    diff = tmp_path / "diff.png"
    _make_image(baseline, (255, 255, 255), size=(10, 10))
    _make_image(actual, (255, 255, 255), size=(12, 10))

    result = compare_image_pair(baseline, actual, diff, threshold=0.02)

    assert result.passed is False
    assert result.difference_ratio == 1.0
    assert result.reason is not None
    assert "Image sizes are different" in result.reason
    assert not diff.exists()


def test_missing_actual_file_fails(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.png"
    actual = tmp_path / "actual.png"
    diff = tmp_path / "diff.png"
    _make_image(baseline, (255, 255, 255))

    result = compare_image_pair(baseline, actual, diff, threshold=0.02)

    assert result.passed is False
    assert result.reason == "Actual image does not exist."


def test_compare_folders_uses_union_of_images(tmp_path: Path) -> None:
    baseline_dir = tmp_path / "baseline"
    actual_dir = tmp_path / "actual"
    diff_dir = tmp_path / "diffs"
    baseline_dir.mkdir()
    actual_dir.mkdir()
    _make_image(baseline_dir / "login.png", (255, 255, 255))
    _make_image(actual_dir / "login.png", (255, 255, 255))
    _make_image(baseline_dir / "settings.png", (255, 255, 255))

    summary = compare_folders(baseline_dir, actual_dir, diff_dir)

    assert summary.total == 2
    assert summary.passed == 1
    assert summary.failed == 1
    assert {result.screen_name for result in summary.results} == {"login.png", "settings.png"}


def test_compare_folders_requires_existing_directories(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Baseline folder does not exist"):
        compare_folders(tmp_path / "missing", tmp_path / "actual", tmp_path / "diffs")


def test_compare_folders_rejects_empty_image_sets(tmp_path: Path) -> None:
    baseline_dir = tmp_path / "baseline"
    actual_dir = tmp_path / "actual"
    baseline_dir.mkdir()
    actual_dir.mkdir()

    with pytest.raises(ValueError, match="No supported images found"):
        compare_folders(baseline_dir, actual_dir, tmp_path / "diffs")


def _make_image(path: Path, color: tuple[int, int, int], size: tuple[int, int] = (8, 8)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)
