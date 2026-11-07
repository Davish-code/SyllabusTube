"""Background job runner, task queues, and progress state tracking."""

from __future__ import annotations

from typing import Any


class JobManager:
    """Manages asynchronous pipeline execution and status reporting."""

    def __init__(self) -> None:
        self.active_jobs: dict[str, dict[str, Any]] = {}

    def start_job(self, pdf_path: str) -> str:
        """Enqueue and launch background execution of the SyllabusTube pipeline."""
        raise NotImplementedError("Background job runner will be implemented in Phase 8.")

    def get_job_status(self, job_id: str) -> dict[str, Any] | None:
        """Return status, stage progress, and completion state of job."""
        raise NotImplementedError("Job status polling will be implemented in Phase 8.")
