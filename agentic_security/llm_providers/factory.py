"""Factory for creating LLM provider instances."""

from typing import Any

from agentic_security.llm_providers.base import BaseLLMProvider, LLMProviderError

# Provider registry mapping name to class
_PROVIDERS: dict[str, type[BaseLLMProvider]] = {}


def _ensure_registered() -> None:
    """Lazy registration of built-in providers."""
    if _PROVIDERS:
        return
    from agentic_security.llm_providers.openai_provider import OpenAIProvider
    from agentic_security.llm_providers.anthropic_provider import AnthropicProvider

    _PROVIDERS["openai"] = OpenAIProvider
    _PROVIDERS["anthropic"] = AnthropicProvider


def register_provider(name: str, provider_class: type[BaseLLMProvider]) -> None:
    """Register a custom provider class."""
    _ensure_registered()
    _PROVIDERS[name.lower()] = provider_class


def get_provider_class(name: str) -> type[BaseLLMProvider]:
    """Get provider class by name."""
    _ensure_registered()
    name_lower = name.lower()
    if name_lower not in _PROVIDERS:
        available = ", ".join(sorted(_PROVIDERS.keys()))
        raise LLMProviderError(f"Unknown provider: {name}. Available: {available}")
    return _PROVIDERS[name_lower]


def list_providers() -> list[str]:
    """List all available provider names."""
    _ensure_registered()
    return sorted(_PROVIDERS.keys())


def create_provider(
    name: str,
    model: str | None = None,
    **kwargs: Any,
) -> BaseLLMProvider:
    """Create a provider instance by name.

    Args:
        name: Provider name ("openai", "anthropic", etc.)
        model: Model name. If None, uses provider's default.
        **kwargs: Additional arguments passed to provider constructor.

    Returns:
        Configured provider instance.

    Raises:
        LLMProviderError: If provider name is unknown.
    """
    provider_class = get_provider_class(name)
    if model is None:
        model = getattr(provider_class, "DEFAULT_MODEL", None)
    if model is None:
        raise LLMProviderError(f"No model specified and {name} has no default")
    return provider_class(model=model, **kwargs)
