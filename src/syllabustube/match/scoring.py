"""Confidence scoring and tier classification."""

from __future__ import annotations

from typing import Literal

from syllabustube.config import TierThresholds


def classify_tier(
    confidence: float,
    verdict: str,
    thresholds: TierThresholds,
) -> Literal["high", "review", "gap"]:
    """Classify match into confidence tiers based on verdict and numeric thresholds.

    Args:
        confidence: Combined similarity and verification score (0.0 to 1.0).
        verdict: Verification verdict ('yes', 'partial', 'no').
        thresholds: High and review thresholds from configuration.

    Returns:
        One of 'high', 'review', or 'gap'.
    """
    if verdict == "no":
        return "gap"
    if verdict == "yes" and confidence >= thresholds.high:
        return "high"
    if confidence >= thresholds.review:
        return "review"
    return "gap"
