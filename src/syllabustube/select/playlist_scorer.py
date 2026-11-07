"""Multi-objective playlist scoring (coverage, focus, order, quality)."""

from __future__ import annotations

from syllabustube.config import SelectionWeights
from syllabustube.models import Match, Playlist, Syllabus


def score_playlist(
    playlist: Playlist,
    syllabus: Syllabus,
    matches: list[Match],
    weights: SelectionWeights,
) -> float:
    """Calculate composite quality score balancing topic coverage, focus, and video order.

    Args:
        playlist: Candidate playlist.
        syllabus: Full course syllabus.
        matches: Verified topic-to-video matches.
        weights: Configured objective weights.

    Returns:
        Weighted score between 0.0 and 1.0.

    Raises:
        NotImplementedError: Phase 6 implementation pending.
    """
    raise NotImplementedError("Playlist scoring will be implemented in Phase 6.")
