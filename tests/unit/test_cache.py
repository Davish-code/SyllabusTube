"""Unit tests for SQLite cache store operations, TTL expiration, and atomic compute."""

import time
from pathlib import Path

from syllabustube.cache.store import CacheStore


def test_cache_set_and_get(tmp_path: Path) -> None:
    db_file = tmp_path / "test_cache.sqlite"
    cache = CacheStore(db_file)

    cache.set("key1", {"message": "hello", "numbers": [1, 2, 3]})
    val = cache.get("key1")
    assert val is not None
    assert val["message"] == "hello"
    assert val["numbers"] == [1, 2, 3]

    cache.close()


def test_cache_delete(tmp_path: Path) -> None:
    db_file = tmp_path / "test_cache.sqlite"
    cache = CacheStore(db_file)

    cache.set("item_to_delete", "value")
    assert cache.get("item_to_delete") == "value"

    deleted = cache.delete("item_to_delete")
    assert deleted is True
    assert cache.get("item_to_delete") is None

    # Deleting non-existent key returns False
    assert cache.delete("non_existent") is False
    cache.close()


def test_cache_ttl_expiration(tmp_path: Path) -> None:
    db_file = tmp_path / "test_cache.sqlite"
    cache = CacheStore(db_file)

    # Set key with short TTL (0.15s)
    cache.set("expiring_key", "temporary", ttl=0.15)
    assert cache.get("expiring_key") == "temporary"

    time.sleep(0.2)
    assert cache.get("expiring_key") is None
    cache.close()


def test_cache_get_or_compute(tmp_path: Path) -> None:
    db_file = tmp_path / "test_cache.sqlite"
    cache = CacheStore(db_file)

    call_count = 0

    def expensive_fn() -> int:
        nonlocal call_count
        call_count += 1
        return 42

    # First call: computes and stores
    res1 = cache.get_or_compute("computed_key", expensive_fn)
    assert res1 == 42
    assert call_count == 1

    # Second call: fetches from cache without executing function
    res2 = cache.get_or_compute("computed_key", expensive_fn)
    assert res2 == 42
    assert call_count == 1

    cache.close()
