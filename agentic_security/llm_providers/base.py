"""Base LLM provider abstraction for unified API access.

Inspired by FuzzyAI's provider architecture, providing a simple interface
for both sync and async LLM interactions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""


class LLMRateLimitError(LLMProviderError):
    """Raised when rate limit is exceeded."""


@dataclass
class LLMMessage:
    """A message in a chat conversation."""
    role: str  # "system", "user", or "assistant"
    content: str


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    model: str | None = None
    finish_reason: str | None = None
    usage: dict[str, int] | None = None


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers.

    Subclasses must implement generate() and chat() methods for both
    sync and async variants.
    """

    def __init__(self, model: str, **kwargs: Any) -> None:
        self.model = model
        self._extra = kwargs

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generate a response from a single prompt."""
        ...

    @abstractmethod
    async def chat(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        """Generate a response from a chat conversation."""
        ...

    @abstractmethod
    def sync_generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Synchronous version of generate()."""
        ...

    @abstractmethod
    def sync_chat(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        """Synchronous version of chat()."""
        ...

    @classmethod
    @abstractmethod
    def get_supported_models(cls) -> list[str]:
        """Return list of supported model names."""
        ...

    async def close(self) -> None:
        """Close any open connections. Override if cleanup is needed."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model!r})"
