"""Anthropic LLM provider implementation."""

import os
from typing import Any

from agentic_security.llm_providers.base import (
    BaseLLMProvider,
    LLMMessage,
    LLMProviderError,
    LLMRateLimitError,
    LLMResponse,
)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic API provider supporting messages API."""

    DEFAULT_MODEL = "claude-3-haiku-20240307"
    API_KEY_ENV = "ANTHROPIC_API_KEY"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(model, **kwargs)
        self.api_key = api_key or os.environ.get(self.API_KEY_ENV)
        if not self.api_key:
            raise LLMProviderError(f"{self.API_KEY_ENV} not set")
        self.base_url = base_url
        self._client: Any = None
        self._async_client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import anthropic
            kwargs: dict[str, Any] = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = anthropic.Anthropic(**kwargs)
        return self._client

    def _get_async_client(self) -> Any:
        if self._async_client is None:
            import anthropic
            kwargs: dict[str, Any] = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._async_client = anthropic.AsyncAnthropic(**kwargs)
        return self._async_client

    @classmethod
    def get_supported_models(cls) -> list[str]:
        return [
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229",
            "claude-3-opus-latest",
            "claude-3-5-haiku-latest",
            "claude-3-5-sonnet-latest",
        ]

    def _messages_to_dicts(
        self, messages: list[LLMMessage]
    ) -> tuple[str | None, list[dict[str, str]]]:
        """Extract system prompt and convert messages to Anthropic format."""
        system_prompt = None
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})
        return system_prompt, chat_messages

    def _parse_response(self, response: Any) -> LLMResponse:
        content = ""
        if response.content:
            block = response.content[0]
            if hasattr(block, "text"):
                content = block.text
        usage = None
        if response.usage:
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        return LLMResponse(
            content=content,
            model=response.model,
            finish_reason=response.stop_reason,
            usage=usage,
        )

    def _handle_error(self, e: Exception) -> None:
        import anthropic
        if isinstance(e, anthropic.RateLimitError):
            raise LLMRateLimitError(str(e)) from e
        if isinstance(e, anthropic.APIError):
            raise LLMProviderError(str(e)) from e
        raise LLMProviderError(str(e)) from e

    async def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        messages = [LLMMessage(role="user", content=prompt)]
        if system_prompt := kwargs.pop("system_prompt", None):
            messages.insert(0, LLMMessage(role="system", content=system_prompt))
        return await self.chat(messages, **kwargs)

    async def chat(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        client = self._get_async_client()
        system_prompt, chat_messages = self._messages_to_dicts(messages)
        create_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": chat_messages,
            "max_tokens": kwargs.pop("max_tokens", 1024),
        }
        if system_prompt:
            create_kwargs["system"] = system_prompt
        create_kwargs.update(kwargs)
        try:
            response = await client.messages.create(**create_kwargs)
            return self._parse_response(response)
        except Exception as e:
            self._handle_error(e)
            raise  # unreachable, but satisfies type checker

    def sync_generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        messages = [LLMMessage(role="user", content=prompt)]
        if system_prompt := kwargs.pop("system_prompt", None):
            messages.insert(0, LLMMessage(role="system", content=system_prompt))
        return self.sync_chat(messages, **kwargs)

    def sync_chat(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        client = self._get_client()
        system_prompt, chat_messages = self._messages_to_dicts(messages)
        create_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": chat_messages,
            "max_tokens": kwargs.pop("max_tokens", 1024),
        }
        if system_prompt:
            create_kwargs["system"] = system_prompt
        create_kwargs.update(kwargs)
        try:
            response = client.messages.create(**create_kwargs)
            return self._parse_response(response)
        except Exception as e:
            self._handle_error(e)
            raise  # unreachable, but satisfies type checker

    async def close(self) -> None:
        if self._async_client:
            await self._async_client.close()
