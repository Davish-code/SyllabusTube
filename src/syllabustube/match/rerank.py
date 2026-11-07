"""Cross-encoder reranking for candidate chunks."""

from __future__ import annotations

from typing import Any

from syllabustube.models import Topic


def rerank_candidates(
    topic: Topic, candidates: list[dict[str, Any]], top_k: int = 5
) -> list[dict[str, Any]]:
    """Rerank retrieved candidate chunks using a cross-encoder model.

    Args:
        topic: Query syllabus topic.
        candidates: Retrieved chunk candidates.
        top_k: Number of highest-ranked items to retain.

    Returns:
        Sorted list of top-k reranked candidates.

    Raises:
        NotImplementedError: Phase 5 implementation pending.
    """
    raise NotImplementedError("Cross-encoder reranker will be implemented in Phase 5.")
