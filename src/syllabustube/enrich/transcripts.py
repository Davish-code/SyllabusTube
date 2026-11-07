"""Captions and transcript fetching via youtube-transcript-api."""

from __future__ import annotations

from syllabustube.models import TranscriptChunk


def fetch_transcript(video_id: str, languages: list[str] | None = None) -> list[TranscriptChunk]:
    """Retrieve official or automated subtitle track for a YouTube video.

    Args:
        video_id: 11-character YouTube video ID.
        languages: Language priority list (defaults to ['en']).

    Returns:
        List of timestamped TranscriptChunk segments.

    Raises:
        NotImplementedError: Phase 3 implementation pending.
    """
    raise NotImplementedError("Transcript fetching will be implemented in Phase 3.")
