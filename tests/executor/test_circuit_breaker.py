"""Tests for CircuitBreaker."""

import pytest
import time
from unittest.mock import patch
from agentic_security.executor.circuit_breaker import CircuitBreaker


class TestCircuitBreaker:
    """Test CircuitBreaker functionality."""

    def test_initialization(self):
        """Test circuit breaker initialization."""
        breaker = CircuitBreaker(failure_threshold=0.5, recovery_timeout=30)

        assert breaker.failure_threshold == 0.5
        assert breaker.recovery_timeout == 30
        assert breaker.state == "closed"
        assert breaker.failures == 0
        assert breaker.successes == 0

    def test_record_success(self):
        """Test recording successful requests."""
        breaker = CircuitBreaker()

        breaker.record_success()
        assert breaker.successes == 1
        assert breaker.failures == 0
        assert breaker.state == "closed"

    def test_record_failure(self):
        """Test recording failed requests."""
        breaker = CircuitBreaker()

        breaker.record_failure()
        assert breaker.failures == 1
        assert breaker.successes == 0
        assert breaker.last_failure_time is not None

    def test_circuit_opens_on_failure_threshold(self):
        """Test that circuit opens when failure threshold is exceeded."""
        breaker = CircuitBreaker(failure_threshold=0.5, recovery_timeout=30)

        # Record 10 requests: 6 failures, 4 successes (60% failure rate)
        for _ in range(4):
            breaker.record_success()
        for _ in range(6):
            breaker.record_failure()

        # Circuit should be open (60% > 50% threshold)
        assert breaker.state == "open"
        assert breaker.is_open() is True

    def test_circuit_stays_closed_below_threshold(self):
        """Test that circuit stays closed when below threshold."""
        breaker = CircuitBreaker(failure_threshold=0.5, recovery_timeout=30)

        # Record 10 requests: 4 failures, 6 successes (40% failure rate)
        for _ in range(6):
            breaker.record_success()
        for _ in range(4):
            breaker.record_failure()

        # Circuit should stay closed (40% < 50% threshold)
        assert breaker.state == "closed"
        assert breaker.is_open() is False

    def test_minimum_sample_size_required(self):
        """Test that minimum sample size is required before opening."""
        breaker = CircuitBreaker(failure_threshold=0.5)

        # Only 5 failures (below minimum of 10 total requests)
        for _ in range(5):
            breaker.record_failure()

        # Circuit should stay closed (not enough samples)
        assert breaker.state == "closed"
        assert breaker.is_open() is False

    def test_circuit_recovery_after_timeout(self):
        """Test that circuit enters half-open state after recovery timeout."""
        breaker = CircuitBreaker(failure_threshold=0.5, recovery_timeout=1)

        # Open the circuit
        for _ in range(4):
            breaker.record_success()
        for _ in range(6):
            breaker.record_failure()

        assert breaker.state == "open"

        # Wait for recovery timeout
        time.sleep(1.1)

        # Check if circuit moves to half-open
        is_open = breaker.is_open()
        assert is_open is False
        assert breaker.state == "half_open"

    def test_half_open_to_closed_on_successes(self):
        """Test that circuit closes from half-open after enough successes."""
        breaker = CircuitBreaker(failure_threshold=0.5, recovery_timeout=1)

        # Open the circuit
        for _ in range(4):
            breaker.record_success()
        for _ in range(6):
            breaker.record_failure()

        # Wait for recovery
        time.sleep(1.1)
        breaker.is_open()  # Triggers transition to half-open

        assert breaker.state == "half_open"

        # Record 3 successes
        breaker.record_success()
        breaker.record_success()
        breaker.record_success()

        # Should transition to closed
        assert breaker.state == "closed"

    def test_get_state(self):
        """Test get_state method."""
        breaker = CircuitBreaker()

        assert breaker.get_state() == "closed"

        # Open the circuit
        for _ in range(10):
            breaker.record_failure()

        assert breaker.get_state() == "open"

    def test_get_failure_rate(self):
        """Test get_failure_rate method."""
        breaker = CircuitBreaker()

        # No requests
        assert breaker.get_failure_rate() == 0.0

        # 3 failures, 7 successes (30% failure rate)
        for _ in range(7):
            breaker.record_success()
        for _ in range(3):
            breaker.record_failure()

        assert breaker.get_failure_rate() == 0.3

    def test_reset(self):
        """Test reset method."""
        breaker = CircuitBreaker()

        # Record some activity
        breaker.record_success()
        breaker.record_failure()
        for _ in range(10):
            breaker.record_failure()

        # Reset
        breaker.reset()

        # Should be back to initial state
        assert breaker.state == "closed"
        assert breaker.failures == 0
        assert breaker.successes == 0
        assert breaker.last_failure_time is None

    def test_exact_failure_threshold(self):
        """Test behavior at exact failure threshold."""
        breaker = CircuitBreaker(failure_threshold=0.5)

        # Exactly 50% failure rate (5 failures, 5 successes)
        for _ in range(5):
            breaker.record_success()
        for _ in range(5):
            breaker.record_failure()

        # Should be open (>= threshold)
        assert breaker.state == "open"

    def test_high_failure_threshold(self):
        """Test with high failure threshold."""
        breaker = CircuitBreaker(failure_threshold=0.9)

        # 80% failure rate (8 failures, 2 successes)
        for _ in range(2):
            breaker.record_success()
        for _ in range(8):
            breaker.record_failure()

        # Should stay closed (80% < 90%)
        assert breaker.state == "closed"

    def test_zero_recovery_timeout(self):
        """Test with zero recovery timeout."""
        breaker = CircuitBreaker(failure_threshold=0.5, recovery_timeout=0)

        # Open the circuit
        for _ in range(10):
            breaker.record_failure()

        assert breaker.state == "open"

        # Should immediately allow recovery attempt
        time.sleep(0.01)
        is_open = breaker.is_open()

        assert is_open is False
        assert breaker.state == "half_open"
