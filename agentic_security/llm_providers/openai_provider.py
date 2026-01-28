"""OpenAI LLM provider implementation."""

import os
from typing import Any

from agentic_security.llm_providers.base import (
    BaseLLMProvider,
    LLMMessage,
    LLMProviderError,
    LLMRateLimitError,
    LLMResponse,
)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider supporting chat completions."""

    DEFAULT_MODEL = "gpt-4o-mini"
    API_KEY_ENV = "OPENAI_API_KEY"

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
            import openai
            self._client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def _get_async_client(self) -> Any:
        if self._async_client is None:
            import openai
            self._async_client = openai.AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._async_client

    @classmethod
    def get_supported_models(cls) -> list[str]:
        return [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-4o-mini",
            "o1-mini",
            "o1-preview",
            "o3-mini",
        ]

    def _messages_to_dicts(self, messages: list[LLMMessage]) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in messages]

    def _parse_response(self, response: Any) -> LLMResponse:
        choice = response.choices[0]
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            finish_reason=choice.finish_reason,
            usage=usage,
        )

    def _handle_error(self, e: Exception) -> None:
        import openai
        if isinstance(e, openai.RateLimitError):
            raise LLMRateLimitError(str(e)) from e
        raise LLMProviderError(str(e)) from e

    async def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        messages = [LLMMessage(role="user", content=prompt)]
        if system_prompt := kwargs.pop("system_prompt", None):
            messages.insert(0, LLMMessage(role="system", content=system_prompt))
        return await self.chat(messages, **kwargs)

    async def chat(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        client = self._get_async_client()
        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=self._messages_to_dicts(messages),
                **kwargs,
            )
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
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=self._messages_to_dicts(messages),
                **kwargs,
            )
            return self._parse_response(response)
        except Exception as e:
            self._handle_error(e)
            raise  # unreachable, but satisfies type checker

    async def close(self) -> None:
        if self._async_client:
            await self._async_client.close()
