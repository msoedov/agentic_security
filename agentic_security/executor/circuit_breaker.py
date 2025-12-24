"""Circuit breaker pattern for fault tolerance."""

import time
from typing import Literal


CircuitState = Literal["closed", "open", "half_open"]


class CircuitBreaker:
    """Circuit breaker to prevent cascading failures.

    Implements the circuit breaker pattern with three states:
    - closed: Normal operation, requests pass through
    - open: Failure threshold exceeded, requests fail fast
    - half_open: Recovery attempt, limited requests allowed

    Example:
        >>> breaker = CircuitBreaker(failure_threshold=0.5, recovery_timeout=30)
        >>> if breaker.is_open():
        ...     raise Exception("Circuit breaker is open")
        >>> try:
        ...     result = make_request()
        ...     breaker.record_success()
        >>> except Exception:
        ...     breaker.record_failure()
    """

    def __init__(self, failure_threshold: float = 0.5, recovery_timeout: int = 30):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Failure rate (0.0-1.0) that triggers open state
            recovery_timeout: Seconds to wait before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.successes = 0
        self.state: CircuitState = "closed"
        self.last_failure_time: float | None = None

    def record_success(self):
        """Record a successful request."""
        self.successes += 1

        # If in half_open state and we have enough successes, close the circuit
        if self.state == "half_open" and self.successes >= 3:
            self.state = "closed"
            self.failures = 0
            self.successes = 0

    def record_failure(self):
        """Record a failed request."""
        self.failures += 1
        self.last_failure_time = time.monotonic()

        total = self.failures + self.successes

        # Need minimum sample size before opening circuit
        if total >= 10:
            failure_rate = self.failures / total
            if failure_rate >= self.failure_threshold:
                self.state = "open"

    def is_open(self) -> bool:
        """Check if circuit breaker is open.

        Returns:
            bool: True if circuit is open and requests should be blocked
        """
        if self.state == "open":
            # Check if we should attempt recovery
            if self.last_failure_time is not None:
                if time.monotonic() - self.last_failure_time > self.recovery_timeout:
                    self.state = "half_open"
                    # Reset counters for half-open state
                    self.failures = 0
                    self.successes = 0
                    return False
            return True

        return False

    def get_state(self) -> CircuitState:
        """Get current circuit breaker state.

        Returns:
            CircuitState: Current state (closed, open, or half_open)
        """
        return self.state

    def get_failure_rate(self) -> float:
        """Get current failure rate.

        Returns:
            float: Failure rate (0.0-1.0), or 0.0 if no requests recorded
        """
        total = self.failures + self.successes
        if total == 0:
            return 0.0
        return self.failures / total

    def reset(self):
        """Reset circuit breaker to initial state."""
        self.failures = 0
        self.successes = 0
        self.state = "closed"
        self.last_failure_time = None
