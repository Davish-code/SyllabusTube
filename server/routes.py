"""REST API endpoints for syllabus upload, pipeline monitoring, and playlist export."""

from __future__ import annotations

from typing import Any


def handle_upload(file_data: bytes, filename: str) -> dict[str, Any]:
    """Endpoint: Upload syllabus PDF and enqueue background pipeline job.

    Raises:
        NotImplementedError: Endpoint implementation pending in Phase 8.
    """
    raise NotImplementedError("Upload endpoint will be implemented in Phase 8.")


def handle_status(job_id: str) -> dict[str, Any]:
    """Endpoint: Poll progress percentage and stage status for an active job.

    Raises:
        NotImplementedError: Endpoint implementation pending in Phase 8.
    """
    raise NotImplementedError("Status endpoint will be implemented in Phase 8.")


def handle_results(job_id: str) -> dict[str, Any]:
    """Endpoint: Retrieve structured syllabus alignment, video matches, and gaps.

    Raises:
        NotImplementedError: Endpoint implementation pending in Phase 8.
    """
    raise NotImplementedError("Results endpoint will be implemented in Phase 8.")


def handle_export(job_id: str, privacy: str = "unlisted") -> dict[str, Any]:
    """Endpoint: Trigger one-click YouTube playlist creation and export.

    Raises:
        NotImplementedError: Endpoint implementation pending in Phase 8.
    """
    raise NotImplementedError("Export endpoint will be implemented in Phase 8.")
