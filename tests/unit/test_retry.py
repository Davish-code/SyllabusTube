"""Unit tests for exponential backoff retry logic and non-retryable exceptions."""

import pytest

from syllabustube.exceptions import NonRetryableError, QuotaExceededError
from syllabustube.utils.retry import retry_with_backoff


def test_retry_eventual_success() -> None:
    attempts = 0

    @retry_with_backoff(max_retries=3, initial_delay=0.01, jitter=False)
    def flappy_operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError("Temporary glitch")
        return "success"

    result = flappy_operation()
    assert result == "success"
    assert attempts == 3


def test_retry_exhaustion_raises() -> None:
    attempts = 0

    @retry_with_backoff(max_retries=2, initial_delay=0.01, jitter=False)
    def consistently_failing() -> None:
        nonlocal attempts
        attempts += 1
        raise TimeoutError("Never responds")

    with pytest.raises(TimeoutError):
        consistently_failing()

    # Initial call + 2 retries = 3 attempts total
    assert attempts == 3


def test_never_retries_quota_exceeded() -> None:
    attempts = 0

    @retry_with_backoff(max_retries=3, initial_delay=0.01)
    def quota_limited_call() -> None:
        nonlocal attempts
        attempts += 1
        raise QuotaExceededError("Daily limit reached", service="youtube")

    with pytest.raises(QuotaExceededError):
        quota_limited_call()

    # Must abort immediately on 1st attempt
    assert attempts == 1


def test_never_retries_non_retryable_error() -> None:
    attempts = 0

    @retry_with_backoff(max_retries=3, initial_delay=0.01)
    def non_retryable_call() -> None:
        nonlocal attempts
        attempts += 1
        raise NonRetryableError("Malformed payload")

    with pytest.raises(NonRetryableError):
        non_retryable_call()

    # Must abort immediately on 1st attempt
    assert attempts == 1
