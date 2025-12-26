"""Tests for ConcurrentExecutor."""

import pytest
import asyncio
from unittest.mock import Mock, patch
from agentic_security.executor.concurrent import ConcurrentExecutor, ExecutorMetrics
from agentic_security.probe_actor.state import FuzzerState


class TestExecutorMetrics:
    """Test ExecutorMetrics functionality."""

    def test_initialization(self):
        """Test metrics initialization."""
        metrics = ExecutorMetrics()

        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.total_latency == 0.0
        assert len(metrics.latencies) == 0

    def test_record_success(self):
        """Test recording successful requests."""
        metrics = ExecutorMetrics()

        metrics.record_success(0.5)
        metrics.record_success(0.3)

        assert metrics.successful_requests == 2
        assert metrics.total_latency == 0.8
        assert len(metrics.latencies) == 2

    def test_record_failure(self):
        """Test recording failed requests."""
        metrics = ExecutorMetrics()

        metrics.record_failure()
        metrics.record_failure()

        assert metrics.failed_requests == 2
        assert metrics.successful_requests == 0

    def test_get_stats_no_requests(self):
        """Test get_stats with no requests."""
        metrics = ExecutorMetrics()

        stats = metrics.get_stats()

        assert stats["total_requests"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["avg_latency_ms"] == 0.0
        assert stats["p95_latency_ms"] == 0.0

    def test_get_stats_with_requests(self):
        """Test get_stats with recorded requests."""
        metrics = ExecutorMetrics()

        # Record some requests
        metrics.record_success(0.1)  # 100ms
        metrics.record_success(0.2)  # 200ms
        metrics.record_success(0.3)  # 300ms
        metrics.record_failure()

        stats = metrics.get_stats()

        assert stats["total_requests"] == 4
        assert stats["successful_requests"] == 3
        assert stats["failed_requests"] == 1
        assert stats["success_rate"] == 0.75
        assert stats["avg_latency_ms"] == pytest.approx(200.0, rel=0.01)

    def test_get_stats_p95_latency(self):
        """Test p95 latency calculation."""
        metrics = ExecutorMetrics()

        # Add 100 requests with varying latencies
        for i in range(100):
            metrics.record_success(i * 0.001)  # 0ms to 99ms

        stats = metrics.get_stats()

        # p95 should be around 95ms
        assert stats["p95_latency_ms"] >= 90.0
        assert stats["p95_latency_ms"] <= 100.0


class TestConcurrentExecutor:
    """Test ConcurrentExecutor functionality."""

    def test_initialization(self):
        """Test executor initialization."""
        executor = ConcurrentExecutor(
            max_concurrent=20,
            rate_limit=10,
            burst=5,
            failure_threshold=0.5,
            recovery_timeout=30,
        )

        assert executor.semaphore._value == 20
        assert executor.rate_limiter.rate == 10
        assert executor.rate_limiter.burst == 5
        assert executor.circuit_breaker.failure_threshold == 0.5
        assert executor.circuit_breaker.recovery_timeout == 30

    @pytest.mark.asyncio
    async def test_execute_batch_success(self):
        """Test successful batch execution."""
        executor = ConcurrentExecutor(max_concurrent=10, rate_limit=100, burst=10)
        fuzzer_state = FuzzerState()

        # Mock request factory
        request_factory = Mock()

        # Mock process_prompt to return success
        async def mock_process_prompt(rf, prompt, tokens, module, state):
            return (10, False)  # 10 tokens, not refused

        with patch(
            "agentic_security.probe_actor.fuzzer.process_prompt",
            side_effect=mock_process_prompt,
        ):
            prompts = ["prompt1", "prompt2", "prompt3"]
            tokens, failures = await executor.execute_batch(
                request_factory, prompts, "test_module", fuzzer_state
            )

        assert tokens == 30  # 3 prompts * 10 tokens
        assert failures == 0

    @pytest.mark.asyncio
    async def test_execute_batch_with_failures(self):
        """Test batch execution with some failures."""
        executor = ConcurrentExecutor(max_concurrent=10, rate_limit=100, burst=10)
        fuzzer_state = FuzzerState()

        request_factory = Mock()

        # Mock process_prompt to alternate success/failure
        call_count = [0]

        async def mock_process_prompt(rf, prompt, tokens, module, state):
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                return (10, True)  # Refused
            return (10, False)  # Success

        with patch(
            "agentic_security.probe_actor.fuzzer.process_prompt",
            side_effect=mock_process_prompt,
        ):
            prompts = ["p1", "p2", "p3", "p4"]
            tokens, failures = await executor.execute_batch(
                request_factory, prompts, "test_module", fuzzer_state
            )

        assert tokens == 40  # 4 prompts * 10 tokens
        assert failures == 2  # 2 refused

    @pytest.mark.asyncio
    async def test_execute_batch_respects_concurrency_limit(self):
        """Test that concurrency limit is respected."""
        executor = ConcurrentExecutor(max_concurrent=2, rate_limit=100, burst=10)
        fuzzer_state = FuzzerState()

        request_factory = Mock()

        # Track concurrent executions
        concurrent_count = [0]
        max_concurrent = [0]

        async def mock_process_prompt(rf, prompt, tokens, module, state):
            concurrent_count[0] += 1
            max_concurrent[0] = max(max_concurrent[0], concurrent_count[0])
            await asyncio.sleep(0.01)  # Simulate work
            concurrent_count[0] -= 1
            return (10, False)

        with patch(
            "agentic_security.probe_actor.fuzzer.process_prompt",
            side_effect=mock_process_prompt,
        ):
            prompts = ["p1", "p2", "p3", "p4", "p5"]
            await executor.execute_batch(
                request_factory, prompts, "test_module", fuzzer_state
            )

        # Max concurrent should not exceed limit
        assert max_concurrent[0] <= 2

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self):
        """Test that circuit breaker opens on failures."""
        executor = ConcurrentExecutor(
            max_concurrent=10,
            rate_limit=100,
            burst=20,
            failure_threshold=0.5,
            recovery_timeout=1,
        )
        fuzzer_state = FuzzerState()
        request_factory = Mock()

        # Mock process_prompt to always fail
        async def mock_process_prompt_fail(rf, prompt, tokens, module, state):
            raise Exception("Request failed")

        # First batch - all failures
        with patch(
            "agentic_security.probe_actor.fuzzer.process_prompt",
            side_effect=mock_process_prompt_fail,
        ):
            prompts = ["p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8", "p9", "p10"]
            tokens, failures = await executor.execute_batch(
                request_factory, prompts, "test_module", fuzzer_state
            )

        # All should have failed
        assert failures == 10

        # Circuit should be open now
        assert executor.circuit_breaker.state == "open"

    @pytest.mark.asyncio
    async def test_get_metrics(self):
        """Test getting executor metrics."""
        executor = ConcurrentExecutor(max_concurrent=10, rate_limit=100, burst=10)
        fuzzer_state = FuzzerState()
        request_factory = Mock()

        async def mock_process_prompt(rf, prompt, tokens, module, state):
            return (10, False)

        with patch(
            "agentic_security.probe_actor.fuzzer.process_prompt",
            side_effect=mock_process_prompt,
        ):
            await executor.execute_batch(
                request_factory, ["p1", "p2"], "test_module", fuzzer_state
            )

        metrics = executor.get_metrics()

        assert "total_requests" in metrics
        assert "success_rate" in metrics
        assert "circuit_breaker_state" in metrics
        assert "available_tokens" in metrics
        assert metrics["total_requests"] == 2
        assert metrics["circuit_breaker_state"] == "closed"

    @pytest.mark.asyncio
    async def test_rate_limiting_applied(self):
        """Test that rate limiting is applied."""
        executor = ConcurrentExecutor(max_concurrent=10, rate_limit=5, burst=2)
        fuzzer_state = FuzzerState()
        request_factory = Mock()

        async def mock_process_prompt(rf, prompt, tokens, module, state):
            return (10, False)

        import time

        with patch(
            "agentic_security.probe_actor.fuzzer.process_prompt",
            side_effect=mock_process_prompt,
        ):
            start = time.monotonic()
            # 5 requests with rate=5/s and burst=2
            # First 2 immediate, next 3 should take ~0.6s total
            await executor.execute_batch(
                request_factory,
                ["p1", "p2", "p3", "p4", "p5"],
                "test_module",
                fuzzer_state,
            )
            elapsed = time.monotonic() - start

        # Should take at least 0.5s (3 requests / 5 per second)
        assert elapsed >= 0.4
