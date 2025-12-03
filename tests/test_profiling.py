"""Tests for profiling utilities."""

import time

from gemini_drive_connector.utils.profiling import PerformanceProfiler, profile_function


def test_performance_profiler() -> None:
    """Test PerformanceProfiler context manager."""
    with PerformanceProfiler("test_operation") as profiler:
        time.sleep(0.1)  # Small delay to ensure timing works
        assert profiler.start_time is not None

    assert profiler.end_time is not None
    assert profiler.duration > 0
    assert profiler.duration < 1.0  # Should be less than 1 second


def test_performance_profiler_duration_property() -> None:
    """Test PerformanceProfiler duration property."""
    profiler = PerformanceProfiler("test")
    assert profiler.duration == 0.0  # Before entering context

    with profiler:
        time.sleep(0.05)

    assert profiler.duration > 0
    assert profiler.duration < 1.0


def test_profile_function_decorator() -> None:
    """Test profile_function decorator."""
    @profile_function(threshold=0.0)  # Low threshold to ensure logging
    def test_function() -> str:
        time.sleep(0.05)
        return "result"

    result = test_function()
    assert result == "result"


def test_memory_profiler() -> None:
    """Test memory_profiler context manager."""
    from gemini_drive_connector.utils.profiling import memory_profiler

    with memory_profiler("test_operation"):
        # Should not raise any exceptions
        pass

