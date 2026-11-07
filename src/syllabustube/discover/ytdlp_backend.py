"""Optional quota-free fallback search using yt-dlp."""

from __future__ import annotations

from syllabustube.models import Playlist


def search_playlists_ytdlp(query: str, max_results: int = 5) -> list[Playlist]:
    """Search YouTube playlists using yt-dlp without consuming YouTube Data API quota.

    Args:
        query: Search term.
        max_results: Maximum playlists to return.

    Returns:
        List of Playlist models.

    Raises:
        NotImplementedError: Phase 2 implementation pending.
    """
    raise NotImplementedError("yt-dlp fallback search backend will be implemented in Phase 2.")
