"""Concurrent executor with rate limiting and circuit breaking."""

import asyncio
import time
from typing import Any

from agentic_security.executor.rate_limiter import TokenBucketRateLimiter
from agentic_security.executor.circuit_breaker import CircuitBreaker
from agentic_security.logutils import logger
from agentic_security.probe_actor.state import FuzzerState


class ExecutorMetrics:
    """Track executor performance metrics."""

    def __init__(self):
        """Initialize metrics tracking."""
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_latency = 0.0
        self.latencies: list[float] = []

    def record_success(self, latency: float):
        """Record a successful request.

        Args:
            latency: Request latency in seconds
        """
        self.successful_requests += 1
        self.total_latency += latency
        self.latencies.append(latency)

    def record_failure(self):
        """Record a failed request."""
        self.failed_requests += 1

    def get_stats(self) -> dict[str, Any]:
        """Get current statistics.

        Returns:
            dict: Statistics including total requests, success rate, latency metrics
        """
        total_requests = self.successful_requests + self.failed_requests

        if total_requests == 0:
            return {
                "total_requests": 0,
                "success_rate": 0.0,
                "avg_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
            }

        success_rate = self.successful_requests / total_requests
        avg_latency_ms = (
            (self.total_latency / self.successful_requests * 1000)
            if self.successful_requests > 0
            else 0.0
        )

        # Calculate p95 latency
        if self.latencies:
            sorted_latencies = sorted(self.latencies)
            p95_index = int(len(sorted_latencies) * 0.95)
            p95_latency_ms = (
                sorted_latencies[p95_index] * 1000
                if p95_index < len(sorted_latencies)
                else 0.0
            )
        else:
            p95_latency_ms = 0.0

        return {
            "total_requests": total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": success_rate,
            "avg_latency_ms": avg_latency_ms,
            "p95_latency_ms": p95_latency_ms,
        }


class ConcurrentExecutor:
    """Enhanced concurrent executor with rate limiting and circuit breaking.

    Provides advanced concurrency control for security scanning with:
    - Token bucket rate limiting
    - Circuit breaker for fault tolerance
    - Metrics collection
    - Semaphore-based concurrency limits

    Example:
        >>> executor = ConcurrentExecutor(max_concurrent=20, rate_limit=10, burst=5)
        >>> tokens, failures = await executor.execute_batch(
        ...     request_factory, prompts, "module_name", fuzzer_state
        ... )
        >>> print(executor.metrics.get_stats())
    """

    def __init__(
        self,
        max_concurrent: int = 50,
        rate_limit: float = 100,
        burst: int = 20,
        failure_threshold: float = 0.5,
        recovery_timeout: int = 30,
    ):
        """Initialize concurrent executor.

        Args:
            max_concurrent: Maximum number of concurrent requests
            rate_limit: Requests per second limit
            burst: Maximum burst size for rate limiter
            failure_threshold: Failure rate that triggers circuit breaker
            recovery_timeout: Seconds before attempting circuit recovery
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.rate_limiter = TokenBucketRateLimiter(rate_limit, burst)
        self.circuit_breaker = CircuitBreaker(failure_threshold, recovery_timeout)
        self.metrics = ExecutorMetrics()

        logger.info(
            f"ConcurrentExecutor initialized: max_concurrent={max_concurrent}, "
            f"rate_limit={rate_limit}/s, burst={burst}"
        )

    async def execute_batch(
        self,
        request_factory,
        prompts: list[str],
        module_name: str,
        fuzzer_state: FuzzerState,
    ) -> tuple[int, int]:
        """Execute a batch of prompts with rate limiting and circuit breaking.

        This is compatible with the existing process_prompt_batch signature.

        Args:
            request_factory: Request factory with fn() method
            prompts: List of prompts to process
            module_name: Name of the module being scanned
            fuzzer_state: State tracking object

        Returns:
            tuple[int, int]: (total_tokens, failures)
        """
        tasks = [
            self._execute_single(request_factory, prompt, module_name, fuzzer_state)
            for prompt in prompts
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        total_tokens = 0
        failures = 0

        for result in results:
            if isinstance(result, Exception):
                failures += 1
                logger.error(f"Task failed with exception: {result}")
            else:
                tokens, refused = result
                total_tokens += tokens
                if refused:
                    failures += 1

        return total_tokens, failures

    async def _execute_single(
        self,
        request_factory,
        prompt: str,
        module_name: str,
        fuzzer_state: FuzzerState,
    ) -> tuple[int, bool]:
        """Execute a single prompt with rate limiting and circuit breaking.

        Args:
            request_factory: Request factory with fn() method
            prompt: Prompt to process
            module_name: Name of the module being scanned
            fuzzer_state: State tracking object

        Returns:
            tuple[int, bool]: (tokens, refused)

        Raises:
            Exception: If circuit breaker is open
        """
        # Rate limiting
        await self.rate_limiter.acquire()

        # Circuit breaker check
        if self.circuit_breaker.is_open():
            self.metrics.record_failure()
            raise Exception("Circuit breaker is open - too many failures")

        # Concurrency control
        async with self.semaphore:
            start_time = time.monotonic()

            try:
                # Import here to avoid circular dependency
                from agentic_security.probe_actor.fuzzer import process_prompt

                tokens = 0  # Initial token count for this prompt
                result = await process_prompt(
                    request_factory, prompt, tokens, module_name, fuzzer_state
                )

                # Record success
                self.circuit_breaker.record_success()
                latency = time.monotonic() - start_time
                self.metrics.record_success(latency)

                return result

            except Exception as e:
                # Record failure
                self.circuit_breaker.record_failure()
                self.metrics.record_failure()
                logger.error(f"Error executing prompt: {e}")
                raise

    def get_metrics(self) -> dict[str, Any]:
        """Get current executor metrics.

        Returns:
            dict: Metrics including request stats, latency, and circuit breaker state
        """
        stats = self.metrics.get_stats()
        stats["circuit_breaker_state"] = self.circuit_breaker.get_state()
        stats["circuit_breaker_failure_rate"] = self.circuit_breaker.get_failure_rate()
        stats["available_tokens"] = self.rate_limiter.get_available_tokens()

        return stats
