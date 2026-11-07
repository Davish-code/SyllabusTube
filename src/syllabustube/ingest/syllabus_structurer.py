"""LLM-powered syllabus structure extraction into Module and Topic objects."""

from __future__ import annotations

from syllabustube.models import Syllabus


def structure_syllabus_text(raw_text: str, subject_hint: str | None = None) -> Syllabus:
    """Transform unformatted syllabus text into structured Syllabus, Module, and Topic domain models.

    Args:
        raw_text: Cleaned text from PDF parsing.
        subject_hint: Optional manual subject override.

    Returns:
        Structured Syllabus instance.

    Raises:
        NotImplementedError: Phase 1 implementation pending.
    """
    raise NotImplementedError("LLM syllabus structuring will be implemented in Phase 1.")
