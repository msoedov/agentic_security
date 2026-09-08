"""Atlas Cloud LLM provider implementation."""

from typing import Any

from agentic_security.llm_providers.openai_provider import OpenAIProvider


class AtlasCloudProvider(OpenAIProvider):
    """Atlas Cloud provider using its OpenAI-compatible chat API."""

    DEFAULT_MODEL = "qwen/qwen3.5-397b-a17b"
    DEFAULT_BASE_URL = "https://api.atlascloud.ai/v1"
    API_KEY_ENV = "ATLASCLOUD_API_KEY"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            **kwargs,
        )

    @classmethod
    def get_supported_models(cls) -> list[str]:
        return [cls.DEFAULT_MODEL]
