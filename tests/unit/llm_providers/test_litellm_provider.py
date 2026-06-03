"""Tests for LiteLLM provider."""

import pytest
from inline_snapshot import snapshot
from unittest.mock import MagicMock, AsyncMock, patch

from agentic_security.llm_providers.litellm_provider import LiteLLMProvider
from agentic_security.llm_providers.base import (
    LLMMessage,
    LLMProviderError,
    LLMRateLimitError,
)


def _mock_response(
    content="Hello",
    model="openai/gpt-4o-mini",
    finish_reason="stop",
    prompt_tokens=10,
    completion_tokens=5,
    total_tokens=15,
):
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = content
    resp.choices[0].finish_reason = finish_reason
    resp.model = model
    resp.usage.prompt_tokens = prompt_tokens
    resp.usage.completion_tokens = completion_tokens
    resp.usage.total_tokens = total_tokens
    return resp


class TestLiteLLMProviderInit:
    def test_default_model(self):
        provider = LiteLLMProvider()
        assert provider.model == snapshot("openai/gpt-4o-mini")

    def test_custom_model(self):
        provider = LiteLLMProvider(model="anthropic/claude-sonnet-4-6")
        assert provider.model == snapshot("anthropic/claude-sonnet-4-6")

    def test_no_api_key_required(self):
        provider = LiteLLMProvider()
        assert provider._api_key is None

    def test_api_key_stored(self):
        provider = LiteLLMProvider(api_key="sk-test")
        assert provider._api_key == snapshot("sk-test")

    def test_api_base_stored(self):
        provider = LiteLLMProvider(api_base="http://localhost:4000")
        assert provider._api_base == snapshot("http://localhost:4000")


class TestLiteLLMProviderCallKwargs:
    def test_drop_params_always_true(self):
        provider = LiteLLMProvider()
        kwargs = provider._call_kwargs()
        assert kwargs["drop_params"] is True

    def test_api_key_forwarded_when_set(self):
        provider = LiteLLMProvider(api_key="sk-test")
        kwargs = provider._call_kwargs()
        assert kwargs["api_key"] == snapshot("sk-test")

    def test_api_key_omitted_when_none(self):
        provider = LiteLLMProvider()
        kwargs = provider._call_kwargs()
        assert "api_key" not in kwargs

    def test_api_base_forwarded_when_set(self):
        provider = LiteLLMProvider(api_base="http://localhost:4000")
        kwargs = provider._call_kwargs()
        assert kwargs["api_base"] == snapshot("http://localhost:4000")

    def test_api_base_omitted_when_none(self):
        provider = LiteLLMProvider()
        kwargs = provider._call_kwargs()
        assert "api_base" not in kwargs

    def test_model_in_kwargs(self):
        provider = LiteLLMProvider(model="groq/llama-3.3-70b-versatile")
        kwargs = provider._call_kwargs()
        assert kwargs["model"] == snapshot("groq/llama-3.3-70b-versatile")


class TestLiteLLMProviderMethods:
    def test_get_supported_models(self):
        models = LiteLLMProvider.get_supported_models()
        assert "openai/gpt-4o" in models
        assert "anthropic/claude-sonnet-4-6" in models

    def test_messages_to_dicts(self):
        provider = LiteLLMProvider()
        messages = [
            LLMMessage(role="system", content="Be helpful"),
            LLMMessage(role="user", content="Hello"),
        ]
        result = provider._messages_to_dicts(messages)
        assert result == snapshot(
            [
                {"role": "system", "content": "Be helpful"},
                {"role": "user", "content": "Hello"},
            ]
        )

    def test_parse_response(self):
        provider = LiteLLMProvider()
        resp = _mock_response(content="Hi!", model="openai/gpt-4o")
        result = provider._parse_response(resp)
        assert result.content == snapshot("Hi!")
        assert result.model == snapshot("openai/gpt-4o")
        assert result.finish_reason == snapshot("stop")
        assert result.usage == snapshot(
            {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        )

    def test_parse_response_null_content(self):
        provider = LiteLLMProvider()
        resp = _mock_response(content=None)
        result = provider._parse_response(resp)
        assert result.content == snapshot("")

    def test_parse_response_no_usage(self):
        provider = LiteLLMProvider()
        resp = _mock_response()
        resp.usage = None
        result = provider._parse_response(resp)
        assert result.usage is None


class TestLiteLLMProviderSync:
    @pytest.fixture
    def provider(self):
        return LiteLLMProvider(model="openai/gpt-4o-mini")

    def test_sync_generate(self, provider):
        resp = _mock_response(content="Sync response")
        with patch(
            "agentic_security.llm_providers.litellm_provider.litellm.completion",
            return_value=resp,
        ) as mock_comp:
            result = provider.sync_generate("Hello")
            assert result.content == snapshot("Sync response")
            call_kwargs = mock_comp.call_args.kwargs
            assert call_kwargs["drop_params"] is True

    def test_sync_chat(self, provider):
        resp = _mock_response(content="Chat response")
        messages = [LLMMessage(role="user", content="Hi")]
        with patch(
            "agentic_security.llm_providers.litellm_provider.litellm.completion",
            return_value=resp,
        ):
            result = provider.sync_chat(messages)
            assert result.content == snapshot("Chat response")

    def test_sync_generate_with_system_prompt(self, provider):
        resp = _mock_response(content="With system")
        with patch(
            "agentic_security.llm_providers.litellm_provider.litellm.completion",
            return_value=resp,
        ) as mock_comp:
            result = provider.sync_generate("Hello", system_prompt="Be brief")
            assert result.content == snapshot("With system")
            messages = mock_comp.call_args.kwargs["messages"]
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == "Be brief"


class TestLiteLLMProviderAsync:
    @pytest.fixture
    def provider(self):
        return LiteLLMProvider(model="anthropic/claude-sonnet-4-6")

    @pytest.mark.asyncio
    async def test_generate(self, provider):
        resp = _mock_response(content="Async response")
        with patch(
            "agentic_security.llm_providers.litellm_provider.litellm.acompletion",
            new_callable=AsyncMock,
            return_value=resp,
        ):
            result = await provider.generate("Hello")
            assert result.content == snapshot("Async response")

    @pytest.mark.asyncio
    async def test_chat(self, provider):
        resp = _mock_response(content="Async chat")
        messages = [LLMMessage(role="user", content="Hi")]
        with patch(
            "agentic_security.llm_providers.litellm_provider.litellm.acompletion",
            new_callable=AsyncMock,
            return_value=resp,
        ) as mock_acomp:
            result = await provider.chat(messages)
            assert result.content == snapshot("Async chat")
            call_kwargs = mock_acomp.call_args.kwargs
            assert call_kwargs["model"] == "anthropic/claude-sonnet-4-6"
            assert call_kwargs["drop_params"] is True


class TestLiteLLMProviderErrors:
    @pytest.fixture
    def provider(self):
        return LiteLLMProvider()

    def test_rate_limit_maps_to_llm_rate_limit_error(self, provider):
        fake_exc = type("RateLimitError", (Exception,), {})()
        fake_exc.__class__.__module__ = "litellm.exceptions"
        fake_exc.__class__.__qualname__ = "RateLimitError"
        with pytest.raises(LLMRateLimitError):
            provider._handle_error(fake_exc)

    def test_generic_error_maps_to_llm_provider_error(self, provider):
        with pytest.raises(LLMProviderError):
            provider._handle_error(Exception("something went wrong"))

    def test_sync_chat_auth_error_raises_provider_error(self, provider):
        with patch(
            "agentic_security.llm_providers.litellm_provider.litellm.completion",
            side_effect=Exception("AuthenticationError: Invalid API key"),
        ):
            with pytest.raises(LLMProviderError, match="Invalid API key"):
                provider.sync_generate("test")

    @pytest.mark.asyncio
    async def test_async_chat_timeout_raises_provider_error(self, provider):
        with patch(
            "agentic_security.llm_providers.litellm_provider.litellm.acompletion",
            new_callable=AsyncMock,
            side_effect=Exception("Timeout: Request timed out"),
        ):
            with pytest.raises(LLMProviderError, match="timed out"):
                await provider.generate("test")

    @pytest.mark.asyncio
    async def test_async_chat_model_not_found_raises_provider_error(self, provider):
        provider = LiteLLMProvider(model="bad/nonexistent-model")
        with patch(
            "agentic_security.llm_providers.litellm_provider.litellm.acompletion",
            new_callable=AsyncMock,
            side_effect=Exception("NotFoundError: Model not found"),
        ):
            with pytest.raises(LLMProviderError, match="not found"):
                await provider.generate("test")


class TestLiteLLMProviderFactory:
    def test_factory_creates_litellm_provider(self):
        from agentic_security.llm_providers.factory import create_provider

        provider = create_provider("litellm")
        assert isinstance(provider, LiteLLMProvider)
        assert provider.model == snapshot("openai/gpt-4o-mini")

    def test_factory_creates_with_custom_model(self):
        from agentic_security.llm_providers.factory import create_provider

        provider = create_provider("litellm", model="groq/llama-3.3-70b-versatile")
        assert provider.model == snapshot("groq/llama-3.3-70b-versatile")

    def test_factory_lists_litellm(self):
        from agentic_security.llm_providers.factory import list_providers

        providers = list_providers()
        assert "litellm" in providers
