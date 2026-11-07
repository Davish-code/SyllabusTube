"""YouTube Data API quota tracking and estimation."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from syllabustube.cache.store import CacheStore
from syllabustube.exceptions import QuotaExceededError

logger = logging.getLogger("syllabustube.utils.quota")

PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


class QuotaTracker:
    """Tracks YouTube Data API v3 units, persists daily totals, and resets at PT midnight."""

    def __init__(
        self,
        cache_store: CacheStore,
        daily_limit: int = 10000,
        search_cost: int = 100,
        list_cost: int = 1,
        insert_cost: int = 50,
    ) -> None:
        self.cache = cache_store
        self.daily_limit = daily_limit
        self.search_cost = search_cost
        self.list_cost = list_cost
        self.insert_cost = insert_cost
        self.costs: dict[str, int] = {
            "search": self.search_cost,
            "list": self.list_cost,
            "insert": self.insert_cost,
        }

    @staticmethod
    def get_pacific_date(dt: datetime | None = None) -> str:
        """Return the current YYYY-MM-DD date string in Pacific Time."""
        if dt is None:
            dt = datetime.now(UTC)
        elif dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(PACIFIC_TZ).strftime("%Y-%m-%d")

    def _get_cache_key(self, date_str: str | None = None) -> str:
        d = date_str or self.get_pacific_date()
        return f"quota_usage:{d}"

    def get_daily_usage(self, date_str: str | None = None) -> dict[str, Any]:
        """Fetch current usage statistics for the specified or current Pacific date."""
        key = self._get_cache_key(date_str)
        data = self.cache.get(key)
        if not data or not isinstance(data, dict):
            return {
                "date": date_str or self.get_pacific_date(),
                "total": 0,
                "by_call_type": {},
            }
        return data

    def used(self) -> int:
        """Return total quota units consumed so far today in Pacific Time."""
        usage = self.get_daily_usage()
        return int(usage.get("total", 0))

    def remaining(self) -> int:
        """Return remaining units for the current Pacific day."""
        return max(0, self.daily_limit - self.used())

    def record(self, call_type: str, units: int | None = None) -> int:
        """Record usage of a given API call type.

        Raises:
            QuotaExceededError: If the planned call exceeds remaining quota.

        Returns:
            New total units consumed today.
        """
        cost = units if units is not None else self.costs.get(call_type, 1)
        current_used = self.used()

        if current_used + cost > self.daily_limit:
            msg = (
                f"Quota exceeded: requested {cost} units for '{call_type}', "
                f"but only {self.remaining()} remaining (limit: {self.daily_limit})."
            )
            logger.error(msg)
            raise QuotaExceededError(message=msg, service="youtube")

        date_str = self.get_pacific_date()
        key = self._get_cache_key(date_str)
        usage = self.get_daily_usage(date_str)

        usage["total"] = current_used + cost
        by_type = usage.setdefault("by_call_type", {})
        by_type[call_type] = by_type.get(call_type, 0) + cost

        # TTL 48 hours to preserve historical record across midnight reset
        self.cache.set(key, usage, ttl=48 * 3600)
        logger.debug(
            "Quota recorded: %s (+%d units). Total used today: %d", call_type, cost, usage["total"]
        )
        return usage["total"]

    def estimate_export(self, n_videos: int) -> int:
        """Estimate the quota required to export a playlist containing n videos.

        Formula: 1 playlist insert + n video inserts (each insert_cost).
        """
        return self.insert_cost + (self.insert_cost * n_videos)
