"""Hybrid dense/sparse retrieval and Reciprocal Rank Fusion (RRF)."""

from __future__ import annotations

from typing import Any

from syllabustube.models import Topic


def hybrid_retrieve(
    topic: Topic, top_k: int = 10, bm25_weight: float = 0.3
) -> list[dict[str, Any]]:
    """Perform hybrid vector + BM25 retrieval for a topic and combine via rank fusion.

    Args:
        topic: Query topic.
        top_k: Number of candidates to retrieve.
        bm25_weight: Relative weighting for sparse retrieval.

    Returns:
        Ranked list of candidate chunk matches.

    Raises:
        NotImplementedError: Phase 5 implementation pending.
    """
    raise NotImplementedError("Hybrid retrieval and RRF will be implemented in Phase 5.")
