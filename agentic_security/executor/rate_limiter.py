"""Token bucket rate limiter for controlling request rate."""

import asyncio
import time


class TokenBucketRateLimiter:
    """Token bucket rate limiter with configurable rate and burst capacity.

    This implements the token bucket algorithm where tokens are added at a fixed
    rate and consumed for each request. Supports bursting up to the bucket capacity.

    Example:
        >>> limiter = TokenBucketRateLimiter(rate=10, burst=20)
        >>> await limiter.acquire()  # Will wait if no tokens available
    """

    def __init__(self, rate: float, burst: int):
        """Initialize rate limiter.

        Args:
            rate: Tokens added per second (requests/sec)
            burst: Maximum bucket capacity (max concurrent burst)
        """
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Acquire a token, waiting if necessary.

        This method will block until a token is available.
        """
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update

            # Add tokens based on elapsed time
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens >= 1:
                # Token available, consume it
                self.tokens -= 1
                return

            # Need to wait for next token
            wait_time = (1 - self.tokens) / self.rate
            await asyncio.sleep(wait_time)
            self.tokens = 0
            self.last_update = time.monotonic()

    def get_available_tokens(self) -> float:
        """Get current number of available tokens (non-blocking).

        Returns:
            float: Number of tokens currently available
        """
        now = time.monotonic()
        elapsed = now - self.last_update
        return min(self.burst, self.tokens + elapsed * self.rate)
