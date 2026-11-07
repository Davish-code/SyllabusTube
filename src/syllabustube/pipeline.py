"""End-to-end SyllabusTube orchestration pipeline."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from syllabustube.config import AppConfig, get_config
from syllabustube.exceptions import SyllabusTubeError
from syllabustube.ingest.pdf_parser import extract_text
from syllabustube.ingest.syllabus_structurer import structure_syllabus
from syllabustube.ingest.validator import ValidationReport, validate_and_repair
from syllabustube.llm import get_llm_client
from syllabustube.llm.base import LLMClient
from syllabustube.models import Match, PipelineResult, Playlist, Syllabus

logger = logging.getLogger("syllabustube.pipeline")

ProgressCallback = Callable[[str, float, str], None]


class Pipeline:
    """Orchestrates the 7 stages of course discovery and playlist curation."""

    def __init__(
        self,
        config: AppConfig | None = None,
        llm_client: LLMClient | None = None,
        hints: dict[str, Any] | None = None,
    ) -> None:
        self.config = config or get_config()
        self.llm = llm_client or get_llm_client(self.config)
        self.hints = hints or {}
        self.last_validation_report: ValidationReport | None = None

    def ingest(
        self,
        pdf_path: str | Path,
        hints: dict[str, Any] | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> Syllabus:
        """Stage 1: Ingest PDF, perform OCR/vision if needed, structure topics via LLM, and validate.

        Args:
            pdf_path: File system path to the input syllabus PDF.
            hints: Optional user overrides for subject and university.
            on_progress: Optional progress callback.

        Returns:
            Validated and structured Syllabus domain model.
        """
        active_hints = {**self.hints, **(hints or {})}
        path = Path(pdf_path)

        # 1. Reading PDF
        if on_progress:
            on_progress("ingest:read", 0.05, f"Reading PDF: {path.name}")
        logger.info("Reading and extracting text from PDF: %s", path)
        doc = extract_text(path, config=self.config, llm_client=self.llm)

        # 2. Transcribing scanned pages
        if doc.scanned_pages:
            msg = f"Transcribing {len(doc.scanned_pages)} scanned page(s) with vision LLM"
            if on_progress:
                on_progress("ingest:ocr", 0.10, msg)
            logger.info(msg)

        # 3. Structuring syllabus
        if on_progress:
            on_progress("ingest:structure", 0.15, "Structuring syllabus with LLM")
        logger.info("Structuring syllabus text into modules and topics...")
        raw_syllabus = structure_syllabus(
            doc=doc,
            llm=self.llm,
            hints=active_hints,
            config=self.config,
        )

        # 4. Validating and repairing
        if on_progress:
            on_progress("ingest:validate", 0.20, "Validating syllabus structure")
        logger.info("Validating structured syllabus...")
        final_syllabus, report = validate_and_repair(
            syllabus=raw_syllabus,
            llm=self.llm,
            page_count=doc.page_count,
            max_retries=self.config.ingest.repair_retries,
        )
        self.last_validation_report = report

        if report.warnings:
            logger.warning("Validation warnings (%d):", len(report.warnings))
            for w in report.warnings:
                logger.warning("  - [%s] %s", w.code, w.message)

        if not report.is_valid:
            logger.error("Validation errors remaining (%d):", len(report.errors))
            for e in report.errors:
                logger.error("  - [%s] %s", e.code, e.message)

        return final_syllabus

    def discover(self, syllabus: Syllabus) -> list[Playlist]:
        """Stage 2: Plan queries per module and discover playlists/videos via YouTube Data API or yt-dlp."""
        raise NotImplementedError(
            "Stage 2 (Discover): YouTube candidate search is not implemented yet."
        )

    def enrich(self, playlists: list[Playlist]) -> list[Playlist]:
        """Stage 3: Fetch captions, chapters, and generate Whisper transcripts if needed."""
        raise NotImplementedError(
            "Stage 3 (Enrich): Transcript and chapter extraction is not implemented yet."
        )

    def index(self, playlists: list[Playlist]) -> Any:
        """Stage 4: Chunk transcripts and index into dense vector store and BM25 index."""
        raise NotImplementedError(
            "Stage 4 (Index): Vector and BM25 indexing is not implemented yet."
        )

    def match(self, syllabus: Syllabus, index_data: Any) -> list[Match]:
        """Stage 5: Hybrid retrieval, cross-encoder rerank, and LLM verification."""
        raise NotImplementedError(
            "Stage 5 (Match): Hybrid retrieval and verification is not implemented yet."
        )

    def select(
        self, syllabus: Syllabus, playlists: list[Playlist], matches: list[Match]
    ) -> list[Playlist]:
        """Stage 6: Multi-objective playlist scoring and greedy set-cover selection."""
        raise NotImplementedError("Stage 6 (Select): Set-cover selection is not implemented yet.")

    def assemble(
        self,
        syllabus: Syllabus,
        selected_playlists: list[Playlist],
        matches: list[Match],
    ) -> PipelineResult:
        """Stage 7: Compile syllabus gaps, generate summary report, and prepare export artifacts."""
        raise NotImplementedError("Stage 7 (Assemble): Report assembly is not implemented yet.")

    def run(
        self,
        pdf_path: str | Path,
        on_progress: ProgressCallback | None = None,
    ) -> PipelineResult:
        """Execute the pipeline from PDF ingestion through playlist assembly."""
        path = Path(pdf_path)
        if not path.exists():
            raise SyllabusTubeError(f"Syllabus file does not exist: {path}")

        logger.info("Starting SyllabusTube pipeline for: %s", path.name)

        try:
            syllabus = self.ingest(path, on_progress=on_progress)

            if on_progress:
                on_progress("discover", 0.30, f"Searching for {len(syllabus.modules)} modules")
            playlists = self.discover(syllabus)

            if on_progress:
                on_progress("enrich", 0.45, "Fetching transcripts")
            enriched = self.enrich(playlists)

            if on_progress:
                on_progress("index", 0.60, "Building indices")
            index_data = self.index(enriched)

            if on_progress:
                on_progress("match", 0.75, "Verifying content matches")
            matches = self.match(syllabus, index_data)

            if on_progress:
                on_progress("select", 0.90, "Optimizing playlist set cover")
            selected = self.select(syllabus, enriched, matches)

            if on_progress:
                on_progress("assemble", 0.95, "Generating final report")
            result = self.assemble(syllabus, selected, matches)

            if on_progress:
                on_progress("complete", 1.0, "Pipeline completed successfully")
            return result

        except NotImplementedError as exc:
            msg = f"Pipeline paused: {exc}"
            logger.info(msg)
            raise SyllabusTubeError(msg) from exc
        except Exception as exc:
            logger.error("Pipeline failed with unexpected error: %s", exc)
            raise
