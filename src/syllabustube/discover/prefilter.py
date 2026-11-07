"""Pre-filtering of candidates by duration, age, video count, and language."""

from __future__ import annotations

from syllabustube.models import Playlist


def prefilter_playlists(
    playlists: list[Playlist],
    min_videos: int = 3,
    max_age_years: int = 5,
    language: str = "en",
) -> list[Playlist]:
    """Filter out short, outdated, empty, or foreign-language candidate playlists.

    Args:
        playlists: Raw candidate playlists.
        min_videos: Minimum video threshold.
        max_age_years: Maximum age limit in years.
        language: Expected primary language code.

    Returns:
        Filtered list of candidate playlists.

    Raises:
        NotImplementedError: Phase 2 implementation pending.
    """
    raise NotImplementedError("Playlist prefiltering will be implemented in Phase 2.")
