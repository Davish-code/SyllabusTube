"""Tests for YouTube export and quota tracking."""

from syllabustube.models import Video
from syllabustube.utils.quota import QuotaTracker


def test_export_quota_calculation() -> None:
    tracker = QuotaTracker(None, insert_cost=50)  # type: ignore[arg-type]
    videos = [
        Video(video_id=f"vid_{i}", title=f"Video {i}", channel="Test Channel") for i in range(5)
    ]
    estimated_units = tracker.estimate_export(len(videos))
    assert estimated_units == 50 + (50 * 5)
