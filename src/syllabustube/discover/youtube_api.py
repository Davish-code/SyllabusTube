"""YouTube Data API v3 client for playlists, playlistItems, and video discovery."""

from __future__ import annotations

from syllabustube.models import Playlist, Video


def search_playlists(
    query: str, max_results: int = 5, api_key: str | None = None
) -> list[Playlist]:
    """Search YouTube for playlists matching a query string.

    Args:
        query: Search term.
        max_results: Maximum playlists to return.
        api_key: Optional API key override.

    Returns:
        List of candidate Playlist models.

    Raises:
        NotImplementedError: Phase 2 implementation pending.
    """
    raise NotImplementedError("YouTube Data API playlist search will be implemented in Phase 2.")


def get_playlist_items(playlist_id: str, api_key: str | None = None) -> list[Video]:
    """Fetch video metadata items for a given playlist ID.

    Args:
        playlist_id: 34-character playlist identifier.
        api_key: Optional API key override.

    Returns:
        List of Video models in order.

    Raises:
        NotImplementedError: Phase 2 implementation pending.
    """
    raise NotImplementedError(
        "YouTube Data API playlist item retrieval will be implemented in Phase 2."
    )
