"""PDF parsing, heading detection, OCR vision fallback, and text normalization."""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import Any

import pymupdf
from pydantic import BaseModel, Field

from syllabustube.config import AppConfig, get_config
from syllabustube.exceptions import SyllabusTubeError
from syllabustube.llm.base import LLMClient

logger = logging.getLogger("syllabustube.ingest.pdf")


class PDFParseError(SyllabusTubeError):
    """Raised when PDF file is invalid, corrupt, encrypted, or exceeds limits."""


class ParsedPage(BaseModel):
    """Extracted text and metadata for a single PDF page."""

    page_number: int = Field(description="1-based page number")
    text: str = Field(description="Cleaned, normalized text content")
    is_scanned: bool = Field(default=False, description="Whether this page required vision OCR")
    char_count: int = Field(default=0, description="Number of non-whitespace characters extracted")
    headings: list[str] = Field(default_factory=list, description="Detected section headings")


class ParsedDocument(BaseModel):
    """Complete parsed document containing pages, full concatenated text, and checksum."""

    pdf_path: str = Field(description="Original file path")
    file_hash: str = Field(description="SHA-256 hash of file content")
    page_count: int = Field(description="Total number of pages")
    pages: list[ParsedPage] = Field(default_factory=list, description="Per-page content")
    full_text: str = Field(description="Concatenated, normalized text across all pages")
    scanned_pages: list[int] = Field(
        default_factory=list, description="List of scanned/OCR page numbers"
    )


def compute_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_ocr_prompt() -> tuple[str, str]:
    """Load the OCR page prompt (system and user template)."""
    prompt_path = Path(__file__).parent.parent / "llm" / "prompts" / "ocr_page.txt"
    if not prompt_path.exists():
        system = "You are an OCR assistant. Transcribe the image into clean text preserving headings and lists."
        user = "Please transcribe this document page image."
        return system, user

    content = prompt_path.read_text(encoding="utf-8")
    system = ""
    user = ""
    if "[SYSTEM]" in content and "[USER]" in content:
        parts = content.split("[USER]")
        system = parts[0].replace("[SYSTEM]", "").strip()
        user = parts[1].strip()
    else:
        user = content.strip()
    return system, user


def _extract_page_blocks(page: pymupdf.Page) -> tuple[str, list[str]]:
    """Extract page text using PyMuPDF block/span info, tagging likely headings.

    Returns:
        Tuple of (formatted_page_text, detected_headings).
    """
    blocks = page.get_text("dict").get("blocks", [])
    text_spans: list[dict[str, Any]] = []

    for b in blocks:
        if b.get("type") == 0:  # Text block
            for line in b.get("lines", []):
                for span in line.get("spans", []):
                    span_text = span.get("text", "").strip()
                    if span_text:
                        text_spans.append(span)

    if not text_spans:
        # Fall back to simple block text
        simple_text = page.get_text("text")
        return simple_text, []

    # Calculate median font size
    sizes = [s.get("size", 10.0) for s in text_spans]
    sizes.sort()
    median_size = sizes[len(sizes) // 2] if sizes else 10.0

    page_lines: list[str] = []
    headings: list[str] = []

    for b in blocks:
        if b.get("type") == 0:
            for line in b.get("lines", []):
                line_parts: list[str] = []
                is_heading = False

                for span in line.get("spans", []):
                    txt = span.get("text", "")
                    size = span.get("size", 10.0)
                    flags = span.get("flags", 0)  # bit 1 or 2 often indicates bold
                    # Flag likely headings: font size >= 1.25 * median or bold with title case
                    if (size >= 1.25 * median_size or (flags & 2 != 0 and len(txt) > 3)) and len(
                        txt
                    ) < 120:
                        is_heading = True
                    line_parts.append(txt)

                combined_line = "".join(line_parts).strip()
                if combined_line:
                    if is_heading:
                        headings.append(combined_line)
                        page_lines.append(f"\n## {combined_line}\n")
                    else:
                        page_lines.append(combined_line)

    return "\n".join(page_lines), headings


def normalize_document_text(pages: list[str]) -> list[str]:
    """Clean up hyphenation across line breaks, repeated headers/footers, and excess spacing."""
    if not pages:
        return []

    # 1. Detect candidate repeated headers or footers across pages
    first_lines: dict[str, int] = {}
    last_lines: dict[str, int] = {}

    for page_text in pages:
        lines = [line.strip() for line in page_text.splitlines() if line.strip()]
        if lines:
            top = lines[0]
            bottom = lines[-1]
            first_lines[top] = first_lines.get(top, 0) + 1
            last_lines[bottom] = last_lines.get(bottom, 0) + 1

    num_pages = len(pages)
    threshold = max(2, int(num_pages * 0.5)) if num_pages > 2 else 999

    repeated_headers = {line for line, cnt in first_lines.items() if cnt >= threshold}
    repeated_footers = {line for line, cnt in last_lines.items() if cnt >= threshold}

    normalized_pages: list[str] = []
    page_num_pattern = re.compile(r"^(?:page\s+)?\d+(?:\s*(?:of|/)\s*\d+)?$", re.IGNORECASE)

    for page_text in pages:
        lines = page_text.splitlines()
        filtered_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            # Strip recurring headers/footers or standalone page numbers
            if stripped in repeated_headers or stripped in repeated_footers:
                continue
            if page_num_pattern.match(stripped):
                continue
            filtered_lines.append(line)

        text = "\n".join(filtered_lines)

        # Fix hyphenated words across line breaks (e.g. "algo-\nrithm" -> "algorithm")
        text = re.sub(r"(\b[A-Za-z]+)-\s*\n\s*([A-Za-z]+\b)", r"\1\2", text)

        # Collapse redundant horizontal spaces
        text = re.sub(r"[ \t]+", " ", text)

        # Collapse excess empty lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        normalized_pages.append(text.strip())

    return normalized_pages


def extract_text(
    pdf_path: str | Path,
    config: AppConfig | None = None,
    llm_client: LLMClient | None = None,
) -> ParsedDocument:
    """Extract text from a syllabus PDF, applying OCR vision fallback on scanned pages.

    Args:
        pdf_path: File system path to syllabus PDF.
        config: Application configuration. If None, uses get_config().
        llm_client: LLM client for vision OCR. If None, vision OCR is skipped.

    Returns:
        ParsedDocument containing page texts, checksum, and full normalized document.

    Raises:
        PDFParseError: On corrupt, encrypted, empty, missing, or excessively large files.
    """
    cfg = config or get_config()
    target_path = Path(pdf_path)

    if not target_path.exists():
        raise PDFParseError(f"PDF file does not exist: {target_path}")

    if target_path.stat().st_size == 0:
        raise PDFParseError(f"PDF file is empty (0 bytes): {target_path}")

    file_hash = compute_sha256(target_path)

    try:
        doc = pymupdf.open(str(target_path))
    except Exception as exc:
        raise PDFParseError(f"Corrupt or invalid PDF file '{target_path.name}': {exc}") from exc

    try:
        if doc.is_encrypted and not doc.authenticate(""):
            raise PDFParseError(
                f"PDF file '{target_path.name}' is password-protected or encrypted."
            )

        page_count = len(doc)
        if page_count == 0:
            raise PDFParseError(f"PDF file '{target_path.name}' contains 0 pages.")

        if page_count > cfg.ingest.max_pages:
            raise PDFParseError(
                f"PDF '{target_path.name}' exceeds maximum configured page limit "
                f"({page_count} > {cfg.ingest.max_pages} pages)."
            )

        raw_page_texts: list[str] = []
        page_headings: list[list[str]] = []
        scanned_flags: list[bool] = []

        min_chars = cfg.ingest.min_chars_per_page
        vision_ocr_enabled = (
            cfg.ingest.vision_ocr and llm_client is not None and llm_client.supports_vision
        )

        ocr_system, ocr_user = load_ocr_prompt()

        for idx, page in enumerate(doc):
            page_num = idx + 1
            extracted_text, headings = _extract_page_blocks(page)
            non_ws_chars = len(re.sub(r"\s+", "", extracted_text))

            if non_ws_chars < min_chars:
                logger.info(
                    "Page %d has only %d non-whitespace characters (threshold: %d).",
                    page_num,
                    non_ws_chars,
                    min_chars,
                )
                if vision_ocr_enabled and llm_client:
                    logger.info("Rendering page %d for Gemini vision OCR...", page_num)
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("png")
                    try:
                        transcribed = llm_client.generate_text(
                            prompt=ocr_user,
                            system=ocr_system,
                            images=[img_bytes],
                        )
                        extracted_text = transcribed.strip()
                        scanned_flags.append(True)
                        logger.info(
                            "Vision OCR transcribed %d characters for page %d.",
                            len(extracted_text),
                            page_num,
                        )
                    except Exception as exc:  # noqa: BLE001
                        logger.warning(
                            "Vision OCR failed on page %d: %s. Using raw text.", page_num, exc
                        )
                        scanned_flags.append(False)
                else:
                    if not vision_ocr_enabled:
                        logger.warning(
                            "Page %d appears to be scanned, but vision OCR is disabled or unavailable.",
                            page_num,
                        )
                    scanned_flags.append(True)
            else:
                scanned_flags.append(False)

            raw_page_texts.append(extracted_text)
            page_headings.append(headings)

        # Normalize texts across pages
        cleaned_page_texts = normalize_document_text(raw_page_texts)

        parsed_pages: list[ParsedPage] = []
        scanned_page_nums: list[int] = []

        for idx, (clean_txt, headings, is_scanned) in enumerate(
            zip(cleaned_page_texts, page_headings, scanned_flags, strict=False)
        ):
            p_num = idx + 1
            char_count = len(re.sub(r"\s+", "", clean_txt))
            if is_scanned:
                scanned_page_nums.append(p_num)

            parsed_pages.append(
                ParsedPage(
                    page_number=p_num,
                    text=clean_txt,
                    is_scanned=is_scanned,
                    char_count=char_count,
                    headings=headings,
                )
            )

        full_text = "\n\n".join(p.text for p in parsed_pages if p.text)

        return ParsedDocument(
            pdf_path=str(target_path),
            file_hash=file_hash,
            page_count=page_count,
            pages=parsed_pages,
            full_text=full_text,
            scanned_pages=scanned_page_nums,
        )
    finally:
        doc.close()
