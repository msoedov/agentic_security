"""Tests for Anthropic provider."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from inline_snapshot import snapshot

from agentic_security.llm_providers.anthropic_provider import AnthropicProvider
from agentic_security.llm_providers.base import LLMMessage, LLMProviderError, LLMRateLimitError


class TestAnthropicProviderInit:
    def test_requires_api_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(LLMProviderError) as exc:
            AnthropicProvider()
        assert "ANTHROPIC_API_KEY" in str(exc.value)

    def test_accepts_api_key_directly(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        provider = AnthropicProvider(api_key="test-key")
        assert provider.api_key == snapshot("test-key")

    def test_uses_env_api_key(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
        provider = AnthropicProvider()
        assert provider.api_key == snapshot("env-key")

    def test_default_model(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        provider = AnthropicProvider()
        assert provider.model == snapshot("claude-3-haiku-20240307")

    def test_custom_model(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        provider = AnthropicProvider(model="claude-3-5-sonnet-latest")
        assert provider.model == snapshot("claude-3-5-sonnet-latest")

    def test_custom_base_url(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        provider = AnthropicProvider(base_url="https://custom.api.com")
        assert provider.base_url == snapshot("https://custom.api.com")


class TestAnthropicProviderMethods:
    @pytest.fixture
    def provider(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        return AnthropicProvider()

    def test_get_supported_models(self, provider):
        models = provider.get_supported_models()
        assert "claude-3-haiku-20240307" in models
        assert "claude-3-5-sonnet-latest" in models

    def test_messages_to_dicts_simple(self, provider):
        messages = [LLMMessage(role="user", content="Hello")]
        system, chat = provider._messages_to_dicts(messages)
        assert system is None
        assert chat == snapshot([{"role": "user", "content": "Hello"}])

    def test_messages_to_dicts_with_system(self, provider):
        messages = [
            LLMMessage(role="system", content="Be helpful"),
            LLMMessage(role="user", content="Hello"),
        ]
        system, chat = provider._messages_to_dicts(messages)
        assert system == snapshot("Be helpful")
        assert chat == snapshot([{"role": "user", "content": "Hello"}])

    def test_messages_to_dicts_multi_turn(self, provider):
        messages = [
            LLMMessage(role="user", content="Hi"),
            LLMMessage(role="assistant", content="Hello!"),
            LLMMessage(role="user", content="How are you?"),
        ]
        system, chat = provider._messages_to_dicts(messages)
        assert system is None
        assert chat == snapshot(
            [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello!"},
                {"role": "user", "content": "How are you?"},
            ]
        )

    def test_parse_response(self, provider):
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Hi there!"
        mock_response.model = "claude-3-haiku-20240307"
        mock_response.stop_reason = "end_turn"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5

        result = provider._parse_response(mock_response)
        assert result.content == snapshot("Hi there!")
        assert result.model == snapshot("claude-3-haiku-20240307")
        assert result.finish_reason == snapshot("end_turn")
        assert result.usage == snapshot({"input_tokens": 10, "output_tokens": 5})

    def test_parse_response_empty_content(self, provider):
        mock_response = MagicMock()
        mock_response.content = []
        mock_response.model = "claude-3-haiku-20240307"
        mock_response.stop_reason = "end_turn"
        mock_response.usage = None

        result = provider._parse_response(mock_response)
        assert result.content == snapshot("")


class TestAnthropicProviderSync:
    @pytest.fixture
    def provider(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        return AnthropicProvider()

    def test_sync_generate(self, provider):
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Response"
        mock_response.model = "claude-3-haiku-20240307"
        mock_response.stop_reason = "end_turn"
        mock_response.usage = None

        with patch.object(provider, "_get_client") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_response
            result = provider.sync_generate("Hello")
            assert result.content == snapshot("Response")

    def test_sync_chat(self, provider):
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Chat response"
        mock_response.model = "claude-3-haiku-20240307"
        mock_response.stop_reason = "end_turn"
        mock_response.usage = None

        messages = [LLMMessage(role="user", content="Hi")]

        with patch.object(provider, "_get_client") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_response
            result = provider.sync_chat(messages)
            assert result.content == snapshot("Chat response")


class TestAnthropicProviderAsync:
    @pytest.fixture
    def provider(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        return AnthropicProvider()

    @pytest.mark.asyncio
    async def test_generate(self, provider):
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Async response"
        mock_response.model = "claude-3-haiku-20240307"
        mock_response.stop_reason = "end_turn"
        mock_response.usage = None

        with patch.object(provider, "_get_async_client") as mock_client:
            mock_client.return_value.messages.create = AsyncMock(
                return_value=mock_response
            )
            result = await provider.generate("Hello")
            assert result.content == snapshot("Async response")

    @pytest.mark.asyncio
    async def test_chat(self, provider):
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Async chat"
        mock_response.model = "claude-3-haiku-20240307"
        mock_response.stop_reason = "end_turn"
        mock_response.usage = None

        messages = [LLMMessage(role="user", content="Hi")]

        with patch.object(provider, "_get_async_client") as mock_client:
            mock_client.return_value.messages.create = AsyncMock(
                return_value=mock_response
            )
            result = await provider.chat(messages)
            assert result.content == snapshot("Async chat")

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self, provider):
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "With system"
        mock_response.model = "claude-3-haiku-20240307"
        mock_response.stop_reason = "end_turn"
        mock_response.usage = None

        with patch.object(provider, "_get_async_client") as mock_client:
            mock_client.return_value.messages.create = AsyncMock(
                return_value=mock_response
            )
            result = await provider.generate("Hello", system_prompt="Be brief")
            assert result.content == snapshot("With system")


class TestAnthropicProviderErrors:
    @pytest.fixture
    def provider(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        return AnthropicProvider()

    def test_handle_rate_limit_error(self, provider):
        import anthropic
        with pytest.raises(LLMRateLimitError):
            provider._handle_error(anthropic.RateLimitError("rate limited", response=MagicMock(), body={}))

    def test_handle_api_error(self, provider):
        import anthropic
        with pytest.raises(LLMProviderError):
            provider._handle_error(anthropic.APIError("api error", request=MagicMock(), body={}))

    def test_handle_generic_error(self, provider):
        with pytest.raises(LLMProviderError):
            provider._handle_error(Exception("something went wrong"))
