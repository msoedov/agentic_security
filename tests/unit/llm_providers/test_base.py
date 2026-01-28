"""Tests for base LLM provider classes."""

import pytest
from inline_snapshot import snapshot

from agentic_security.llm_providers.base import (
    BaseLLMProvider,
    LLMMessage,
    LLMProviderError,
    LLMRateLimitError,
    LLMResponse,
)


class TestLLMMessage:
    def test_create_message(self):
        msg = LLMMessage(role="user", content="hello")
        assert msg.role == snapshot("user")
        assert msg.content == snapshot("hello")

    def test_system_message(self):
        msg = LLMMessage(role="system", content="You are helpful")
        assert msg.role == snapshot("system")


class TestLLMResponse:
    def test_minimal_response(self):
        resp = LLMResponse(content="Hello!")
        assert resp.content == snapshot("Hello!")
        assert resp.model is None
        assert resp.finish_reason is None
        assert resp.usage is None

    def test_full_response(self):
        resp = LLMResponse(
            content="Hi there",
            model="gpt-4o",
            finish_reason="stop",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )
        assert resp.content == snapshot("Hi there")
        assert resp.model == snapshot("gpt-4o")
        assert resp.finish_reason == snapshot("stop")
        assert resp.usage == snapshot(
            {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        )


class TestExceptions:
    def test_provider_error_is_exception(self):
        with pytest.raises(LLMProviderError):
            raise LLMProviderError("test error")

    def test_rate_limit_error_is_provider_error(self):
        with pytest.raises(LLMProviderError):
            raise LLMRateLimitError("rate limited")

    def test_rate_limit_error_specific_catch(self):
        with pytest.raises(LLMRateLimitError):
            raise LLMRateLimitError("rate limited")


class TestBaseLLMProvider:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            BaseLLMProvider(model="test")  # type: ignore

    def test_repr_format(self):
        # Create a concrete implementation for testing
        class ConcreteProvider(BaseLLMProvider):
            async def generate(self, prompt, **kwargs):
                return LLMResponse(content="")

            async def chat(self, messages, **kwargs):
                return LLMResponse(content="")

            def sync_generate(self, prompt, **kwargs):
                return LLMResponse(content="")

            def sync_chat(self, messages, **kwargs):
                return LLMResponse(content="")

            @classmethod
            def get_supported_models(cls):
                return ["test-model"]

        provider = ConcreteProvider(model="test-model")
        assert repr(provider) == snapshot("ConcreteProvider(model='test-model')")
