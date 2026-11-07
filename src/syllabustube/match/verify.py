"""LLM verification of topic coverage with evidence extraction."""

from __future__ import annotations

from typing import Any

from syllabustube.models import Match, Topic


def verify_match_with_llm(topic: Topic, candidate_chunk: dict[str, Any]) -> Match:
    """Prompt an LLM to judge if the video chunk covers the topic (yes/partial/no) and cite evidence.

    Args:
        topic: Syllabus topic.
        candidate_chunk: Candidate video transcript chunk with timestamps.

    Returns:
        Structured Match object with verdict, confidence, and quote.

    Raises:
        NotImplementedError: Phase 5 implementation pending.
    """
    raise NotImplementedError("LLM match verification will be implemented in Phase 5.")
