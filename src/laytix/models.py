"""Shared data models for Laytix."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ComparisonResult:
    """Result of comparing one baseline image with one actual image."""

    screen_name: str
    baseline_path: Path
    actual_path: Path
    diff_path: Path | None
    difference_ratio: float
    threshold: float
    passed: bool
    reason: str | None = None


@dataclass(frozen=True)
class ComparisonSummary:
    """Summary for a folder comparison run."""

    project_name: str
    results: list[ComparisonResult]
    report_path: Path | None = None

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for result in self.results if result.passed)

    @property
    def failed(self) -> int:
        return self.total - self.passed

    @property
    def has_failures(self) -> bool:
        return self.failed > 0
