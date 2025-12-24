"""Tests for TokenBucketRateLimiter."""

import asyncio
import pytest
import time
from unittest.mock import patch
from agentic_security.executor.rate_limiter import TokenBucketRateLimiter


class TestTokenBucketRateLimiter:
    """Test TokenBucketRateLimiter functionality."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test rate limiter initialization."""
        limiter = TokenBucketRateLimiter(rate=10, burst=20)

        assert limiter.rate == 10
        assert limiter.burst == 20
        assert limiter.tokens == 20  # Starts full

    @pytest.mark.asyncio
    async def test_acquire_with_available_tokens(self):
        """Test acquiring tokens when they're available."""
        limiter = TokenBucketRateLimiter(rate=10, burst=5)

        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start

        # Should return immediately
        assert elapsed < 0.1
        assert limiter.tokens < 5  # One token consumed

    @pytest.mark.asyncio
    async def test_acquire_waits_when_no_tokens(self):
        """Test that acquire waits when no tokens available."""
        limiter = TokenBucketRateLimiter(rate=10, burst=1)

        # Consume the initial token
        await limiter.acquire()

        # Next acquire should wait
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start

        # Should wait approximately 1/rate seconds (0.1s for rate=10)
        assert elapsed >= 0.08  # Allow some tolerance

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test that rate limiting actually limits request rate."""
        limiter = TokenBucketRateLimiter(rate=10, burst=2)

        # Make 5 requests
        start = time.monotonic()
        for _ in range(5):
            await limiter.acquire()
        elapsed = time.monotonic() - start

        # With rate=10/s and burst=2:
        # - First 2 requests are immediate (burst)
        # - Next 3 requests require waiting: 3 * (1/10) = 0.3s
        # Total should be around 0.3s
        assert elapsed >= 0.25  # Allow some tolerance
        assert elapsed < 0.5

    @pytest.mark.asyncio
    async def test_burst_capacity(self):
        """Test that burst capacity allows immediate requests."""
        limiter = TokenBucketRateLimiter(rate=5, burst=10)

        # Make burst number of requests immediately
        start = time.monotonic()
        for _ in range(10):
            await limiter.acquire()
        elapsed = time.monotonic() - start

        # All 10 requests should be nearly immediate (using burst capacity)
        assert elapsed < 0.2

    @pytest.mark.asyncio
    async def test_token_replenishment(self):
        """Test that tokens are replenished over time."""
        limiter = TokenBucketRateLimiter(rate=10, burst=5)

        # Consume all tokens
        for _ in range(5):
            await limiter.acquire()

        assert limiter.tokens < 1

        # Wait for tokens to replenish
        await asyncio.sleep(0.3)  # Should add 3 tokens at rate=10

        # Should have tokens again (approximately 3)
        available = limiter.get_available_tokens()
        assert available >= 2.5
        assert available <= 3.5

    @pytest.mark.asyncio
    async def test_get_available_tokens(self):
        """Test get_available_tokens method."""
        limiter = TokenBucketRateLimiter(rate=10, burst=5)

        # Initially full
        assert limiter.get_available_tokens() == 5

        # After consuming one
        await limiter.acquire()
        assert limiter.get_available_tokens() < 5

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test rate limiter with concurrent requests."""
        limiter = TokenBucketRateLimiter(rate=10, burst=3)

        async def make_request(limiter):
            await limiter.acquire()
            return time.monotonic()

        # Make 5 concurrent requests
        start = time.monotonic()
        tasks = [make_request(limiter) for _ in range(5)]
        timestamps = await asyncio.gather(*tasks)
        total_elapsed = time.monotonic() - start

        # First 3 should be immediate (burst=3)
        # Next 2 should wait
        # Total time should be around 0.2s (2 * 1/10)
        assert total_elapsed >= 0.15
        assert total_elapsed < 0.4

    @pytest.mark.asyncio
    async def test_max_burst_capacity(self):
        """Test that tokens don't exceed burst capacity."""
        limiter = TokenBucketRateLimiter(rate=100, burst=5)

        # Wait longer than needed to fill
        await asyncio.sleep(0.2)  # Would add 20 tokens, but capped at 5

        # Check tokens don't exceed burst
        available = limiter.get_available_tokens()
        assert available <= 5
        assert available >= 4.5  # Close to full
