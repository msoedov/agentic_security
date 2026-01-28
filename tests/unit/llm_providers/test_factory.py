"""Tests for LLM provider factory."""

import pytest
from inline_snapshot import snapshot

from agentic_security.llm_providers.factory import (
    create_provider,
    get_provider_class,
    list_providers,
    register_provider,
)
from agentic_security.llm_providers.base import (
    BaseLLMProvider,
    LLMProviderError,
    LLMResponse,
)


class TestListProviders:
    def test_includes_builtin_providers(self):
        providers = list_providers()
        assert "openai" in providers
        assert "anthropic" in providers

    def test_returns_sorted_list(self):
        providers = list_providers()
        assert providers == sorted(providers)


class TestGetProviderClass:
    def test_get_openai(self):
        from agentic_security.llm_providers.openai_provider import OpenAIProvider

        cls = get_provider_class("openai")
        assert cls is OpenAIProvider

    def test_get_anthropic(self):
        from agentic_security.llm_providers.anthropic_provider import AnthropicProvider

        cls = get_provider_class("anthropic")
        assert cls is AnthropicProvider

    def test_case_insensitive(self):
        cls1 = get_provider_class("OpenAI")
        cls2 = get_provider_class("OPENAI")
        cls3 = get_provider_class("openai")
        assert cls1 is cls2 is cls3

    def test_unknown_provider_raises(self):
        with pytest.raises(LLMProviderError) as exc:
            get_provider_class("unknown")
        assert "Unknown provider: unknown" in str(exc.value)
        assert "Available:" in str(exc.value)


class TestRegisterProvider:
    def test_register_custom_provider(self):
        class CustomProvider(BaseLLMProvider):
            async def generate(self, prompt, **kwargs):
                return LLMResponse(content="custom")

            async def chat(self, messages, **kwargs):
                return LLMResponse(content="custom")

            def sync_generate(self, prompt, **kwargs):
                return LLMResponse(content="custom")

            def sync_chat(self, messages, **kwargs):
                return LLMResponse(content="custom")

            @classmethod
            def get_supported_models(cls):
                return ["custom-model"]

        register_provider("custom", CustomProvider)
        assert "custom" in list_providers()
        assert get_provider_class("custom") is CustomProvider


class TestCreateProvider:
    def test_create_openai_with_default_model(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        provider = create_provider("openai")
        assert provider.model == snapshot("gpt-4o-mini")

    def test_create_openai_with_custom_model(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        provider = create_provider("openai", model="gpt-4o")
        assert provider.model == snapshot("gpt-4o")

    def test_create_anthropic_with_default_model(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        provider = create_provider("anthropic")
        assert provider.model == snapshot("claude-3-haiku-20240307")

    def test_create_anthropic_with_custom_model(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        provider = create_provider("anthropic", model="claude-3-5-sonnet-latest")
        assert provider.model == snapshot("claude-3-5-sonnet-latest")

    def test_create_with_api_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        provider = create_provider("openai", api_key="direct-key")
        assert provider.api_key == snapshot("direct-key")

    def test_create_unknown_provider_raises(self):
        with pytest.raises(LLMProviderError):
            create_provider("unknown")

    def test_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        provider = create_provider("OpenAI")
        assert provider.__class__.__name__ == snapshot("OpenAIProvider")
