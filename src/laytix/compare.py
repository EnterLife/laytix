"""Image comparison logic for Laytix."""

from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image, ImageChops
from skimage.metrics import structural_similarity

from laytix.models import ComparisonResult, ComparisonSummary

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SUPPORTED_COMPARISON_METHODS = {"pixel", "ssim"}
ComparisonMethod = Literal["pixel", "ssim"]


def compare_image_pair(
    baseline_path: Path | str,
    actual_path: Path | str,
    diff_path: Path | str | None,
    *,
    threshold: float = 0.02,
    method: ComparisonMethod = "pixel",
    screen_name: str | None = None,
) -> ComparisonResult:
    """Compare two images and optionally write a visual diff image."""

    baseline = Path(baseline_path)
    actual = Path(actual_path)
    diff = Path(diff_path) if diff_path is not None else None
    name = screen_name or baseline.stem
    _validate_comparison_method(method)

    if not baseline.exists():
        return _failed_result(name, baseline, actual, diff, threshold, "Baseline image does not exist.")

    if not actual.exists():
        return _failed_result(name, baseline, actual, diff, threshold, "Actual image does not exist.")

    with Image.open(baseline) as baseline_image, Image.open(actual) as actual_image:
        baseline_rgb = baseline_image.convert("RGB")
        actual_rgb = actual_image.convert("RGB")

        if baseline_rgb.size != actual_rgb.size:
            reason = (
                "Image sizes are different: "
                f"baseline={baseline_rgb.size[0]}x{baseline_rgb.size[1]}, "
                f"actual={actual_rgb.size[0]}x{actual_rgb.size[1]}."
            )
            return _failed_result(name, baseline, actual, diff, threshold, reason)

        if method == "pixel":
            diff_image = ImageChops.difference(baseline_rgb, actual_rgb)
            difference_ratio = _calculate_difference_ratio(diff_image)
            visual_diff = _make_visual_diff(diff_image)
        else:
            difference_ratio, visual_diff = _compare_with_ssim(baseline_rgb, actual_rgb)

        if diff is not None:
            diff.parent.mkdir(parents=True, exist_ok=True)
            visual_diff.save(diff)

        passed = difference_ratio <= threshold
        reason = None if passed else "Difference ratio exceeds threshold."

        return ComparisonResult(
            screen_name=name,
            baseline_path=baseline,
            actual_path=actual,
            diff_path=diff,
            difference_ratio=difference_ratio,
            threshold=threshold,
            passed=passed,
            reason=reason,
        )


def compare_folders(
    baseline_dir: Path | str,
    actual_dir: Path | str,
    diff_dir: Path | str,
    *,
    threshold: float = 0.02,
    method: ComparisonMethod = "pixel",
    project_name: str = "Laytix project",
) -> ComparisonSummary:
    """Compare matching images from two folders by relative file path."""

    baseline_root = Path(baseline_dir)
    actual_root = Path(actual_dir)
    diff_root = Path(diff_dir)
    _validate_comparison_method(method)

    if not baseline_root.exists():
        raise FileNotFoundError(f"Baseline folder does not exist: {baseline_root}")

    if not actual_root.exists():
        raise FileNotFoundError(f"Actual folder does not exist: {actual_root}")

    relative_paths = sorted(_collect_image_paths(baseline_root) | _collect_image_paths(actual_root))
    if not relative_paths:
        raise ValueError(
            "No supported images found. Add PNG, JPG, JPEG, or WEBP screenshots to baseline and actual folders."
        )

    results = []

    for relative_path in relative_paths:
        baseline_path = baseline_root / relative_path
        actual_path = actual_root / relative_path
        diff_path = diff_root / relative_path.with_suffix(".diff.png")
        screen_name = relative_path.as_posix()
        results.append(
            compare_image_pair(
                baseline_path,
                actual_path,
                diff_path,
                threshold=threshold,
                method=method,
                screen_name=screen_name,
            )
        )

    return ComparisonSummary(project_name=project_name, results=results)


def _collect_image_paths(root: Path) -> set[Path]:
    return {
        path.relative_to(root)
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    }


def _calculate_difference_ratio(diff_image: Image.Image) -> float:
    data = diff_image.tobytes()
    changed_pixels = sum(
        1
        for index in range(0, len(data), 3)
        if data[index] != 0 or data[index + 1] != 0 or data[index + 2] != 0
    )
    width, height = diff_image.size
    return changed_pixels / (width * height)


def _compare_with_ssim(baseline_image: Image.Image, actual_image: Image.Image) -> tuple[float, Image.Image]:
    baseline_array = np.asarray(baseline_image)
    actual_array = np.asarray(actual_image)
    win_size = _ssim_window_size(min(baseline_image.size))

    score, ssim_map = structural_similarity(
        baseline_array,
        actual_array,
        channel_axis=2,
        data_range=255,
        full=True,
        win_size=win_size,
    )
    difference_ratio = max(0.0, min(1.0, 1.0 - float(score)))
    visual_diff = _make_ssim_visual_diff(ssim_map)
    return difference_ratio, visual_diff


def _ssim_window_size(shortest_side: int) -> int:
    if shortest_side < 3:
        raise ValueError("SSIM comparison requires images at least 3x3 pixels.")

    return min(7, shortest_side if shortest_side % 2 == 1 else shortest_side - 1)


def _make_ssim_visual_diff(ssim_map: np.ndarray) -> Image.Image:
    if ssim_map.ndim == 3:
        ssim_map = ssim_map.mean(axis=2)

    difference = np.clip(1.0 - ssim_map, 0.0, 1.0)
    intensity = (difference * 255).astype(np.uint8)
    output = np.zeros((*intensity.shape, 3), dtype=np.uint8)
    output[:, :, 0] = intensity
    return Image.fromarray(output, "RGB")


def _make_visual_diff(diff_image: Image.Image) -> Image.Image:
    red = Image.new("RGB", diff_image.size, (255, 0, 0))
    mask = diff_image.convert("L").point(lambda value: 255 if value else 0)
    output = Image.new("RGB", diff_image.size, (0, 0, 0))
    output.paste(red, mask=mask)
    return output


def _validate_comparison_method(method: str) -> None:
    if method not in SUPPORTED_COMPARISON_METHODS:
        supported = ", ".join(sorted(SUPPORTED_COMPARISON_METHODS))
        raise ValueError(f"Comparison method must be one of: {supported}.")


def _failed_result(
    screen_name: str,
    baseline_path: Path,
    actual_path: Path,
    diff_path: Path | None,
    threshold: float,
    reason: str,
) -> ComparisonResult:
    return ComparisonResult(
        screen_name=screen_name,
        baseline_path=baseline_path,
        actual_path=actual_path,
        diff_path=diff_path,
        difference_ratio=1.0,
        threshold=threshold,
        passed=False,
        reason=reason,
    )
