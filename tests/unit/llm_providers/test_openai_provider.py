"""Tests for OpenAI provider."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from inline_snapshot import snapshot

from agentic_security.llm_providers.openai_provider import OpenAIProvider
from agentic_security.llm_providers.base import LLMMessage, LLMProviderError, LLMRateLimitError


class TestOpenAIProviderInit:
    def test_requires_api_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(LLMProviderError) as exc:
            OpenAIProvider()
        assert "OPENAI_API_KEY" in str(exc.value)

    def test_accepts_api_key_directly(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        provider = OpenAIProvider(api_key="test-key")
        assert provider.api_key == snapshot("test-key")

    def test_uses_env_api_key(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")
        provider = OpenAIProvider()
        assert provider.api_key == snapshot("env-key")

    def test_default_model(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        provider = OpenAIProvider()
        assert provider.model == snapshot("gpt-4o-mini")

    def test_custom_model(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        provider = OpenAIProvider(model="gpt-4o")
        assert provider.model == snapshot("gpt-4o")

    def test_custom_base_url(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        provider = OpenAIProvider(base_url="https://custom.api.com")
        assert provider.base_url == snapshot("https://custom.api.com")


class TestOpenAIProviderMethods:
    @pytest.fixture
    def provider(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        return OpenAIProvider()

    def test_get_supported_models(self, provider):
        models = provider.get_supported_models()
        assert "gpt-4o" in models
        assert "gpt-4o-mini" in models
        assert "gpt-3.5-turbo" in models

    def test_messages_to_dicts(self, provider):
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

    def test_parse_response(self, provider):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hi there!"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4o"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        result = provider._parse_response(mock_response)
        assert result.content == snapshot("Hi there!")
        assert result.model == snapshot("gpt-4o")
        assert result.finish_reason == snapshot("stop")
        assert result.usage == snapshot(
            {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        )

    def test_parse_response_empty_content(self, provider):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4o"
        mock_response.usage = None

        result = provider._parse_response(mock_response)
        assert result.content == snapshot("")


class TestOpenAIProviderSync:
    @pytest.fixture
    def provider(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        return OpenAIProvider()

    def test_sync_generate(self, provider):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4o-mini"
        mock_response.usage = None

        with patch.object(provider, "_get_client") as mock_client:
            mock_client.return_value.chat.completions.create.return_value = mock_response
            result = provider.sync_generate("Hello")
            assert result.content == snapshot("Response")

    def test_sync_chat(self, provider):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Chat response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4o-mini"
        mock_response.usage = None

        messages = [LLMMessage(role="user", content="Hi")]

        with patch.object(provider, "_get_client") as mock_client:
            mock_client.return_value.chat.completions.create.return_value = mock_response
            result = provider.sync_chat(messages)
            assert result.content == snapshot("Chat response")


class TestOpenAIProviderAsync:
    @pytest.fixture
    def provider(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        return OpenAIProvider()

    @pytest.mark.asyncio
    async def test_generate(self, provider):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Async response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4o-mini"
        mock_response.usage = None

        with patch.object(provider, "_get_async_client") as mock_client:
            mock_client.return_value.chat.completions.create = AsyncMock(
                return_value=mock_response
            )
            result = await provider.generate("Hello")
            assert result.content == snapshot("Async response")

    @pytest.mark.asyncio
    async def test_chat(self, provider):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Async chat"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4o-mini"
        mock_response.usage = None

        messages = [LLMMessage(role="user", content="Hi")]

        with patch.object(provider, "_get_async_client") as mock_client:
            mock_client.return_value.chat.completions.create = AsyncMock(
                return_value=mock_response
            )
            result = await provider.chat(messages)
            assert result.content == snapshot("Async chat")

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self, provider):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "With system"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4o-mini"
        mock_response.usage = None

        with patch.object(provider, "_get_async_client") as mock_client:
            mock_client.return_value.chat.completions.create = AsyncMock(
                return_value=mock_response
            )
            result = await provider.generate("Hello", system_prompt="Be brief")
            assert result.content == snapshot("With system")


class TestOpenAIProviderErrors:
    @pytest.fixture
    def provider(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        return OpenAIProvider()

    def test_handle_rate_limit_error(self, provider):
        import openai
        with pytest.raises(LLMRateLimitError):
            provider._handle_error(openai.RateLimitError("rate limited", response=MagicMock(), body={}))

    def test_handle_generic_error(self, provider):
        with pytest.raises(LLMProviderError):
            provider._handle_error(Exception("something went wrong"))
