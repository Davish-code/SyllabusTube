"""Custom exceptions for SyllabusTube."""

from typing import Any


class SyllabusTubeError(Exception):
    """Base exception for all SyllabusTube errors."""


class NonRetryableError(SyllabusTubeError):
    """Exception indicating an operation failed permanently and should not be retried."""


class QuotaExceededError(NonRetryableError):
    """Exception raised when API quota (e.g. YouTube Data API or Gemini) is exceeded."""

    def __init__(
        self,
        message: str = "API quota exceeded",
        service: str | None = None,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.service = service
        self.details = details
