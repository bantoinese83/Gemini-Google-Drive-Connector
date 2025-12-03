"""Performance profiling utilities."""

import functools
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

from loguru import logger  # type: ignore[import-untyped]


class PerformanceProfiler:
    """Context manager for profiling code blocks."""

    def __init__(self, operation_name: str, log_threshold: float = 1.0) -> None:
        """Initialize profiler.

        Args:
            operation_name: Name of the operation being profiled
            log_threshold: Minimum duration in seconds to log (default: 1.0)
        """
        self.operation_name = operation_name
        self.log_threshold = log_threshold
        self.start_time: float | None = None
        self.end_time: float | None = None

    def __enter__(self) -> "PerformanceProfiler":
        """Start profiling."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """End profiling and log if threshold exceeded."""
        self.end_time = time.perf_counter()
        duration = self.end_time - (self.start_time or 0)

        if duration >= self.log_threshold:
            logger.debug(f"⏱️  {self.operation_name} took {duration:.2f}s")

    @property
    def duration(self) -> float:
        """Get duration in seconds."""
        if self.start_time is None or self.end_time is None:
            return 0.0
        return self.end_time - self.start_time


def profile_function(threshold: float = 1.0) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to profile function execution time.

    Args:
        threshold: Minimum duration in seconds to log

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with PerformanceProfiler(f"{func.__name__}()", threshold):
                return func(*args, **kwargs)

        return wrapper

    return decorator


@contextmanager
def memory_profiler(operation_name: str) -> Iterator[None]:
    """Context manager for basic memory profiling.

    Args:
        operation_name: Name of the operation being profiled

    Yields:
        None
    """
    try:
        yield
        # Basic memory check - can be enhanced with memory_profiler package
        # For full memory profiling, install: pip install memory-profiler
        logger.debug(f"💾 Memory check for {operation_name}")
    except ImportError:
        # If memory profiling not available, just pass through
        yield
