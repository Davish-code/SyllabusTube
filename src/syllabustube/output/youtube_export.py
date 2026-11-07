"""Resumable one-click export creating YouTube playlists via authenticated API."""

from __future__ import annotations

from syllabustube.models import Video


def export_course_playlist(
    title: str,
    description: str,
    videos: list[Video],
    privacy_status: str = "unlisted",
    client_secret_file: str | None = None,
) -> str:
    """Create a new playlist on user's YouTube channel and add videos sequentially.

    Args:
        title: Playlist title.
        description: Course syllabus description.
        videos: Ordered list of videos.
        privacy_status: 'unlisted', 'public', or 'private'.
        client_secret_file: Path to client_secret.json.

    Returns:
        URL of newly created YouTube playlist.

    Raises:
        NotImplementedError: Phase 7 implementation pending.
    """
    raise NotImplementedError("YouTube playlist export will be implemented in Phase 7.")
