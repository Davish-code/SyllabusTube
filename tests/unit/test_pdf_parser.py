"""Unit tests for PyMuPDF text extraction, normalization, and OCR fallback."""

from pathlib import Path

import pymupdf
import pytest

from syllabustube.config import AppConfig
from syllabustube.ingest.pdf_parser import (
    PDFParseError,
    extract_text,
    normalize_document_text,
)
from syllabustube.llm.base import LLMClient


class MockVisionLLM(LLMClient):
    supports_vision: bool = True

    def __init__(self, ocr_output: str = "Transcribed Unit 1: Introduction to Matrices") -> None:
        self.ocr_output = ocr_output
        self.ocr_calls = 0

    def _raw_generate_text(
        self, prompt: str, system: str | None = None, images: list[bytes] | None = None
    ) -> str:
        self.ocr_calls += 1
        return self.ocr_output

    def _raw_generate_json(
        self,
        prompt: str,
        schema: dict[str, any] | None = None,
        system: str | None = None,
        images: list[bytes] | None = None,
    ) -> str:
        return "{}"


def create_sample_pdf(path: Path, pages_text: list[str]) -> Path:
    """Helper to create a temporary PDF with PyMuPDF."""
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page()
        page.insert_text((50, 72), text, fontsize=12)
    doc.save(str(path))
    doc.close()
    return path


def test_extract_text_normal_pdf(tmp_path: Path) -> None:
    pdf_file = tmp_path / "normal_syllabus.pdf"
    content = [
        "COURSE: Computer Networks\nUnit 1: Physical Layer\nTransmission media and topology.",
        "Unit 2: Data Link Layer\nFraming, error detection and flow control.",
    ]
    create_sample_pdf(pdf_file, content)

    doc = extract_text(pdf_file)
    assert doc.page_count == 2
    assert "Computer Networks" in doc.full_text
    assert "Physical Layer" in doc.full_text
    assert "Data Link Layer" in doc.full_text
    assert len(doc.scanned_pages) == 0


def test_repeated_headers_and_footers_stripped() -> None:
    raw_pages = [
        "Department of Computer Science\nUnit 1: Algorithms\nPage 1 of 3",
        "Department of Computer Science\nUnit 2: Graphs\nPage 2 of 3",
        "Department of Computer Science\nUnit 3: Dynamic Programming\nPage 3 of 3",
    ]
    cleaned = normalize_document_text(raw_pages)
    for page in cleaned:
        assert "Department of Computer Science" not in page
        assert "Page 1 of 3" not in page
    assert "Unit 1: Algorithms" in cleaned[0]
    assert "Unit 2: Graphs" in cleaned[1]


def test_hyphenation_normalized() -> None:
    text = ["We will study the algo-\nrithm and opti-\nmization."]
    cleaned = normalize_document_text(text)
    assert "algorithm" in cleaned[0]
    assert "optimization" in cleaned[0]


def test_scanned_low_text_page_triggers_vision_ocr(tmp_path: Path) -> None:
    pdf_file = tmp_path / "scanned_syllabus.pdf"
    # Page 1 normal, Page 2 nearly empty (simulating scanned image)
    pages = [
        "Syllabus: Deep Learning\nCourse Code: CS501",
        "X",  # Only 1 char, triggers low-text threshold
    ]
    create_sample_pdf(pdf_file, pages)

    mock_llm = MockVisionLLM(ocr_output="Transcribed: Unit 2 Neural Networks and Backpropagation")
    cfg = AppConfig()
    cfg.ingest.min_chars_per_page = 20

    doc = extract_text(pdf_file, config=cfg, llm_client=mock_llm)
    assert doc.page_count == 2
    assert 2 in doc.scanned_pages
    assert mock_llm.ocr_calls == 1
    assert "Neural Networks" in doc.full_text


def test_empty_pdf_raises_error(tmp_path: Path) -> None:
    empty_file = tmp_path / "empty.pdf"
    empty_file.write_bytes(b"")

    with pytest.raises(PDFParseError) as exc_info:
        extract_text(empty_file)
    assert "0 bytes" in str(exc_info.value)


def test_corrupt_pdf_raises_error(tmp_path: Path) -> None:
    corrupt_file = tmp_path / "corrupt.pdf"
    corrupt_file.write_bytes(b"%PDF-1.4 not a real valid pdf document data")

    with pytest.raises(PDFParseError) as exc_info:
        extract_text(corrupt_file)
    assert "Corrupt or invalid PDF" in str(exc_info.value)
