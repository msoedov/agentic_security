"""LiteLLM provider — unified access to 100+ LLM backends."""

from typing import Any

try:
    import litellm
except ImportError:
    litellm = None

from agentic_security.llm_providers.base import (
    BaseLLMProvider,
    LLMMessage,
    LLMProviderError,
    LLMRateLimitError,
    LLMResponse,
)


class LiteLLMProvider(BaseLLMProvider):
    """LLM provider using LiteLLM SDK for 100+ backends.

    Accepts any LiteLLM model string (e.g. ``openai/gpt-4o``,
    ``anthropic/claude-sonnet-4-6``, ``groq/llama-3.3-70b-versatile``).
    """

    DEFAULT_MODEL = "openai/gpt-4o-mini"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        api_base: str | None = None,
        **kwargs: Any,
    ) -> None:
        if litellm is None:
            raise LLMProviderError(
                "litellm is not installed. Install it with: pip install litellm"
            )
        super().__init__(model, **kwargs)
        self._api_key = api_key
        self._api_base = api_base

    def _call_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"model": self.model, "drop_params": True}
        if self._api_key:
            kwargs["api_key"] = self._api_key
        if self._api_base:
            kwargs["api_base"] = self._api_base
        return kwargs

    @classmethod
    def get_supported_models(cls) -> list[str]:
        return [
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "anthropic/claude-sonnet-4-6",
            "anthropic/claude-haiku-4-5",
            "groq/llama-3.3-70b-versatile",
            "together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo",
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
            model=getattr(response, "model", self.model),
            finish_reason=choice.finish_reason,
            usage=usage,
        )

    def _handle_error(self, e: Exception) -> None:
        if litellm is not None and isinstance(e, litellm.exceptions.RateLimitError):
            raise LLMRateLimitError(str(e)) from e
        raise LLMProviderError(str(e)) from e

    async def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        messages = [LLMMessage(role="user", content=prompt)]
        if system_prompt := kwargs.pop("system_prompt", None):
            messages.insert(0, LLMMessage(role="system", content=system_prompt))
        return await self.chat(messages, **kwargs)

    async def chat(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        try:
            response = await litellm.acompletion(
                messages=self._messages_to_dicts(messages),
                **{**self._call_kwargs(), **kwargs},
            )
            return self._parse_response(response)
        except Exception as e:
            self._handle_error(e)
            raise

    def sync_generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        messages = [LLMMessage(role="user", content=prompt)]
        if system_prompt := kwargs.pop("system_prompt", None):
            messages.insert(0, LLMMessage(role="system", content=system_prompt))
        return self.sync_chat(messages, **kwargs)

    def sync_chat(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        try:
            response = litellm.completion(
                messages=self._messages_to_dicts(messages),
                **{**self._call_kwargs(), **kwargs},
            )
            return self._parse_response(response)
        except Exception as e:
            self._handle_error(e)
            raise
