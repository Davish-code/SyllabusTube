"""Sliding-window text chunker preserving video timestamps."""

from __future__ import annotations

from syllabustube.models import TranscriptChunk


def chunk_transcript(
    chunks: list[TranscriptChunk],
    chunk_words: int = 150,
    chunk_overlap: int = 30,
) -> list[TranscriptChunk]:
    """Group subtitle sentences into overlapping timestamped chunks.

    Args:
        chunks: Granular subtitle segments.
        chunk_words: Target word count per chunk.
        chunk_overlap: Overlapping word count between contiguous chunks.

    Returns:
        List of merged overlapping TranscriptChunk models.

    Raises:
        NotImplementedError: Phase 4 implementation pending.
    """
    raise NotImplementedError("Transcript chunking will be implemented in Phase 4.")
