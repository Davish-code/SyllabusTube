"""Retry logic with exponential backoff and jitter."""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable, Sequence
from functools import wraps
from typing import Any, TypeVar

from syllabustube.exceptions import NonRetryableError, QuotaExceededError

T = TypeVar("T")
logger = logging.getLogger("syllabustube.utils.retry")


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Sequence[type[Exception]] = (Exception,),
    non_retryable_exceptions: Sequence[type[Exception]] = (QuotaExceededError, NonRetryableError),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retrying a function with exponential backoff and jitter.

    Never retries QuotaExceededError or NonRetryableError (or subclasses).

    Args:
        max_retries: Maximum number of retry attempts after initial failure.
        initial_delay: Delay in seconds before first retry.
        backoff_factor: Multiplier applied to delay each attempt.
        jitter: If True, adds random jitter between 0 and 0.5 * current_delay.
        retryable_exceptions: Exception types to retry.
        non_retryable_exceptions: Exception types that abort immediately.
    """
    non_retryable_tuple = tuple(non_retryable_exceptions)
    retryable_tuple = tuple(retryable_exceptions)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except non_retryable_tuple as exc:
                    logger.warning("Permanent error encountered: %s; not retrying.", exc)
                    raise
                except retryable_tuple as exc:
                    last_exception = exc
                    if attempt == max_retries:
                        logger.error(
                            "Function '%s' failed after %d attempts: %s",
                            func.__name__,
                            max_retries + 1,
                            exc,
                        )
                        raise

                    sleep_time = delay
                    if jitter:
                        sleep_time += random.uniform(0, 0.5 * delay)

                    logger.warning(
                        "Attempt %d/%d for '%s' failed with %s: %s. Retrying in %.2fs...",
                        attempt + 1,
                        max_retries + 1,
                        func.__name__,
                        type(exc).__name__,
                        exc,
                        sleep_time,
                    )
                    time.sleep(sleep_time)
                    delay *= backoff_factor

            if last_exception:
                raise last_exception
            raise RuntimeError(f"Unexpected termination in retry loop for {func.__name__}")

        return wrapper

    return decorator
