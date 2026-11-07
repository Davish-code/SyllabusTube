"""Unit tests for YouTube Data API quota tracking and estimation."""

from pathlib import Path

import pytest

from syllabustube.cache.store import CacheStore
from syllabustube.exceptions import QuotaExceededError
from syllabustube.utils.quota import QuotaTracker


def test_quota_initial_state(tmp_path: Path) -> None:
    cache = CacheStore(tmp_path / "quota_test.sqlite")
    tracker = QuotaTracker(cache, daily_limit=10000, search_cost=100, list_cost=1, insert_cost=50)

    assert tracker.used() == 0
    assert tracker.remaining() == 10000
    cache.close()


def test_quota_record_and_persistence(tmp_path: Path) -> None:
    db_file = tmp_path / "quota_test.sqlite"
    cache1 = CacheStore(db_file)
    tracker1 = QuotaTracker(cache1, daily_limit=10000)

    tracker1.record("search")  # 100
    tracker1.record("list")  # 1
    assert tracker1.used() == 101
    assert tracker1.remaining() == 9899
    cache1.close()

    # Re-open with new CacheStore instance to verify SQLite persistence
    cache2 = CacheStore(db_file)
    tracker2 = QuotaTracker(cache2, daily_limit=10000)
    assert tracker2.used() == 101
    cache2.close()


def test_estimate_export() -> None:
    tracker = QuotaTracker(None, insert_cost=50)  # type: ignore[arg-type]
    # 1 playlist insert (50) + 10 video inserts (10 * 50 = 500) = 550
    assert tracker.estimate_export(10) == 550
    assert tracker.estimate_export(0) == 50


def test_quota_exceeded_raises(tmp_path: Path) -> None:
    cache = CacheStore(tmp_path / "quota_test.sqlite")
    tracker = QuotaTracker(cache, daily_limit=150, search_cost=100)

    tracker.record("search")  # used: 100
    # Next search requires 100, which exceeds 150 limit
    with pytest.raises(QuotaExceededError):
        tracker.record("search")

    cache.close()


def test_pacific_midnight_reset(tmp_path: Path) -> None:
    cache = CacheStore(tmp_path / "quota_test.sqlite")
    tracker = QuotaTracker(cache, daily_limit=10000)

    # Simulate usage on Day 1
    day1_usage = {"date": "2026-11-06", "total": 9500, "by_call_type": {"search": 9500}}
    cache.set("quota_usage:2026-11-06", day1_usage)

    # If queried for Day 1
    assert tracker.get_daily_usage("2026-11-06")["total"] == 9500

    # For Day 2, usage is independent / reset
    assert tracker.get_daily_usage("2026-11-07")["total"] == 0

    cache.close()
