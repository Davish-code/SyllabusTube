"""Local automatic speech-to-text fallback using OpenAI Whisper."""

from __future__ import annotations

from syllabustube.models import TranscriptChunk


def transcribe_video_audio(video_id: str, audio_path: str | None = None) -> list[TranscriptChunk]:
    """Download audio and perform local transcription when subtitles are missing.

    Args:
        video_id: 11-character YouTube video ID.
        audio_path: Optional path to pre-downloaded audio track.

    Returns:
        List of generated TranscriptChunk segments.

    Raises:
        NotImplementedError: Phase 3 implementation pending.
    """
    raise NotImplementedError("Whisper speech-to-text fallback will be implemented in Phase 3.")
