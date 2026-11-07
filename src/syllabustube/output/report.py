"""JSON and Markdown alignment report generation."""

from __future__ import annotations

from pathlib import Path

from syllabustube.models import PipelineResult


def generate_markdown_report(result: PipelineResult) -> str:
    """Format PipelineResult into human-readable Markdown with gap analysis.

    Args:
        result: Completed pipeline result.

    Returns:
        Markdown report string.

    Raises:
        NotImplementedError: Phase 7 implementation pending.
    """
    raise NotImplementedError("Markdown report generation will be implemented in Phase 7.")


def save_reports(result: PipelineResult, output_dir: str | Path) -> None:
    """Save both JSON and Markdown alignment reports to disk.

    Args:
        result: Completed pipeline result.
        output_dir: Destination directory.

    Raises:
        NotImplementedError: Phase 7 implementation pending.
    """
    raise NotImplementedError("Report export will be implemented in Phase 7.")

