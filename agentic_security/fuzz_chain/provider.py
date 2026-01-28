from typing import Protocol, Any


class LLMProvider(Protocol):
    """Protocol for LLM providers that can be used in FuzzChain."""

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate response from LLM. Returns the response text."""
        ...
