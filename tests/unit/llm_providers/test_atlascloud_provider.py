"""Tests for the Atlas Cloud provider."""

import pytest
from inline_snapshot import snapshot

from agentic_security.llm_providers.atlascloud_provider import AtlasCloudProvider
from agentic_security.llm_providers.base import LLMProviderError


class TestAtlasCloudProviderInit:
    def test_requires_api_key(self, monkeypatch):
        monkeypatch.delenv("ATLASCLOUD_API_KEY", raising=False)
        with pytest.raises(LLMProviderError) as exc:
            AtlasCloudProvider()
        assert "ATLASCLOUD_API_KEY" in str(exc.value)

    def test_uses_atlas_defaults(self, monkeypatch):
        monkeypatch.setenv("ATLASCLOUD_API_KEY", "test-key")
        provider = AtlasCloudProvider()
        assert provider.api_key == snapshot("test-key")
        assert provider.model == snapshot("qwen/qwen3.5-397b-a17b")
        assert provider.base_url == snapshot("https://api.atlascloud.ai/v1")

    def test_accepts_overrides(self, monkeypatch):
        monkeypatch.delenv("ATLASCLOUD_API_KEY", raising=False)
        provider = AtlasCloudProvider(
            model="custom/model",
            api_key="direct-key",
            base_url="https://example.com/v1",
        )
        assert provider.model == snapshot("custom/model")
        assert provider.api_key == snapshot("direct-key")
        assert provider.base_url == snapshot("https://example.com/v1")

    def test_supported_models_includes_default(self, monkeypatch):
        monkeypatch.setenv("ATLASCLOUD_API_KEY", "test-key")
        provider = AtlasCloudProvider()
        assert provider.get_supported_models() == snapshot(["qwen/qwen3.5-397b-a17b"])
