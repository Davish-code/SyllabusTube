"""PDF extraction with OCR and vision fallback."""

from __future__ import annotations

from pathlib import Path


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Extract raw text from a syllabus PDF, falling back to OCR/vision if scanned.

    Args:
        pdf_path: Path to the input PDF file.

    Returns:
        Extracted plain text content.

    Raises:
        NotImplementedError: Phase 1 implementation pending.
    """
    raise NotImplementedError("PDF text extraction will be implemented in Phase 1.")

