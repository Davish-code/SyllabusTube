"""End-to-end SyllabusTube orchestration pipeline."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from syllabustube.config import AppConfig, get_config
from syllabustube.exceptions import SyllabusTubeError
from syllabustube.models import Match, PipelineResult, Playlist, Syllabus

logger = logging.getLogger("syllabustube.pipeline")

ProgressCallback = Callable[[str, float, str], None]


class Pipeline:
    """Orchestrates the 7 stages of course discovery and playlist curation."""

    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or get_config()

    def ingest(self, pdf_path: str | Path) -> Syllabus:
        """Stage 1: Ingest PDF, perform OCR/vision if needed, and structure topics via LLM."""
        raise NotImplementedError(
            "Stage 1 (Ingest): PDF parsing and structuring is not implemented yet."
        )

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
        """Execute the pipeline from PDF ingestion through playlist assembly.

        Args:
            pdf_path: File system path to the input syllabus PDF.
            on_progress: Optional callback taking (stage_name, percent_float, status_message).

        Returns:
            Completed PipelineResult.

        Raises:
            SyllabusTubeError: If a stage fails or is not yet implemented.
        """
        path = Path(pdf_path)
        if not path.exists():
            raise SyllabusTubeError(f"Syllabus file does not exist: {path}")

        logger.info("Starting SyllabusTube pipeline for: %s", path.name)

        try:
            if on_progress:
                on_progress("ingest", 0.05, f"Reading {path.name}")
            syllabus = self.ingest(path)

            if on_progress:
                on_progress("discover", 0.20, f"Searching for {len(syllabus.modules)} modules")
            playlists = self.discover(syllabus)

            if on_progress:
                on_progress("enrich", 0.35, "Fetching transcripts")
            enriched = self.enrich(playlists)

            if on_progress:
                on_progress("index", 0.50, "Building indices")
            index_data = self.index(enriched)

            if on_progress:
                on_progress("match", 0.70, "Verifying content matches")
            matches = self.match(syllabus, index_data)

            if on_progress:
                on_progress("select", 0.85, "Optimizing playlist set cover")
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
