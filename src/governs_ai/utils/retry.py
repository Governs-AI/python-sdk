# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2026 GovernsAI. All rights reserved.
"""
Retry utilities for the GovernsAI Python SDK.
"""

import asyncio
import functools
from dataclasses import dataclass
from typing import Callable, Any, Optional
from ..exceptions.base import GovernsAIError


class RetryCondition:
    """Base class for retry conditions."""

    def should_retry(self, error: Exception) -> bool:
        """Determine if an error should trigger a retry."""
        return False


class RetryableErrorCondition(RetryCondition):
    """Retry on retryable GovernsAI errors."""

    def should_retry(self, error: Exception) -> bool:
        """Retry if error is retryable."""
        return isinstance(error, GovernsAIError) and error.retryable


class NetworkErrorCondition(RetryCondition):
    """Retry on network errors."""

    def should_retry(self, error: Exception) -> bool:
        """Retry on network-related errors."""
        return isinstance(error, (ConnectionError, TimeoutError, OSError))


class StatusCodeCondition(RetryCondition):
    """Retry on specific status codes."""

    def __init__(self, status_codes: list[int]):
        """Initialize with status codes to retry on."""
        self.status_codes = status_codes

    def should_retry(self, error: Exception) -> bool:
        """Retry if error has specific status code."""
        if isinstance(error, GovernsAIError) and error.status_code:
            return error.status_code in self.status_codes
        return False


class CustomRetryCondition(RetryCondition):
    """Custom retry condition."""

    def __init__(self, condition_func: Callable[[Exception], bool]):
        """Initialize with custom condition function."""
        self.condition_func = condition_func

    def should_retry(self, error: Exception) -> bool:
        """Use custom condition."""
        return self.condition_func(error)


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    retry_delay: float = 1.0
    backoff_factor: float = 2.0
    max_delay: float = 60.0
    jitter: bool = True
    retry_condition: Optional[RetryCondition] = None

    def __post_init__(self):
        """Set default retry condition if none provided."""
        if self.retry_condition is None:
            self.retry_condition = RetryableErrorCondition()


def with_retry(
    retry_config: Optional[RetryConfig] = None,
    retry_condition: Optional[RetryCondition] = None,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
):
    """
    Decorator for adding retry logic to async functions.

    Args:
        retry_config: Complete retry configuration
        retry_condition: Condition for when to retry
        max_retries: Maximum number of retries
        retry_delay: Initial delay between retries
        backoff_factor: Factor to multiply delay by after each retry
        max_delay: Maximum delay between retries
        jitter: Whether to add random jitter to delays

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Use provided config or create from parameters
            if retry_config:
                config = retry_config
            else:
                config = RetryConfig(
                    max_retries=max_retries,
                    retry_delay=retry_delay,
                    backoff_factor=backoff_factor,
                    max_delay=max_delay,
                    jitter=jitter,
                    retry_condition=retry_condition or RetryableErrorCondition(),
                )
            condition = config.retry_condition or RetryableErrorCondition()

            last_error = None
            delay = config.retry_delay

            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e

                    # Check if we should retry
                    if attempt < config.max_retries and condition.should_retry(e):
                        # Calculate delay with backoff
                        if config.jitter:
                            import random

                            jitter_factor = random.uniform(0.5, 1.5)
                            actual_delay = delay * jitter_factor
                        else:
                            actual_delay = delay

                        # Cap delay at max_delay
                        actual_delay = min(actual_delay, config.max_delay)

                        # Wait before retry
                        await asyncio.sleep(actual_delay)

                        # Increase delay for next retry
                        delay *= config.backoff_factor
                    else:
                        # Don't retry, re-raise the error
                        raise e

            # If we get here, all retries failed
            if last_error is not None:
                raise last_error
            raise RuntimeError(
                "Retry wrapper exited without a result or captured error"
            )

        return wrapper

    return decorator


def retry_on_network_error(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
):
    """
    Convenience decorator for retrying on network errors.

    Args:
        max_retries: Maximum number of retries
        retry_delay: Initial delay between retries
        backoff_factor: Factor to multiply delay by after each retry
        max_delay: Maximum delay between retries
        jitter: Whether to add random jitter to delays

    Returns:
        Decorated function with network error retry logic
    """
    return with_retry(
        retry_condition=NetworkErrorCondition(),
        max_retries=max_retries,
        retry_delay=retry_delay,
        backoff_factor=backoff_factor,
        max_delay=max_delay,
        jitter=jitter,
    )


def retry_on_status_code(
    status_codes: list[int],
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
):
    """
    Convenience decorator for retrying on specific status codes.

    Args:
        status_codes: List of status codes to retry on
        max_retries: Maximum number of retries
        retry_delay: Initial delay between retries
        backoff_factor: Factor to multiply delay by after each retry
        max_delay: Maximum delay between retries
        jitter: Whether to add random jitter to delays

    Returns:
        Decorated function with status code retry logic
    """
    return with_retry(
        retry_condition=StatusCodeCondition(status_codes),
        max_retries=max_retries,
        retry_delay=retry_delay,
        backoff_factor=backoff_factor,
        max_delay=max_delay,
        jitter=jitter,
    )
