"""Unit tests for LLM-based refusal classifier."""

from unittest.mock import MagicMock

import pytest
from inline_snapshot import snapshot

from agentic_security.refusal_classifier.llm_classifier import (
    LLMRefusalClassifier,
    build_evaluation_prompt,
    create_llm_classifier,
    DEFAULT_PASS_CONDITIONS,
    DEFAULT_FAIL_CONDITIONS,
)


class MockLLMClient:
    """Mock LLM client for testing."""

    def __init__(self, response: str = "fail"):
        self.response = response
        self.calls: list[tuple[str, str]] = []

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        return self.response


class TestBuildEvaluationPrompt:

    def test_build_with_defaults(self):
        result = build_evaluation_prompt("Hello, I can help with that.")
        assert "Pass conditions (attack succeeded):" in result
        assert "Fail conditions (model refused):" in result
        assert "Hello, I can help with that." in result

    def test_build_with_custom_conditions(self):
        result = build_evaluation_prompt(
            "test output",
            pass_conditions=["Custom pass 1"],
            fail_conditions=["Custom fail 1"],
        )
        assert "Custom pass 1" in result
        assert "Custom fail 1" in result

    def test_build_with_empty_output(self):
        result = build_evaluation_prompt("")
        assert "<empty response>" in result

    def test_default_conditions_exist(self):
        assert len(DEFAULT_PASS_CONDITIONS) == snapshot(4)
        assert len(DEFAULT_FAIL_CONDITIONS) == snapshot(6)


class TestLLMRefusalClassifier:

    def test_is_refusal_pass_response(self):
        client = MockLLMClient(response="pass")
        classifier = LLMRefusalClassifier(client=client)
        # "pass" means attack succeeded, so is_refusal returns False
        assert classifier.is_refusal("Here's how to do that...") is False

    def test_is_refusal_fail_response(self):
        client = MockLLMClient(response="fail")
        classifier = LLMRefusalClassifier(client=client)
        # "fail" means model refused, so is_refusal returns True
        assert classifier.is_refusal("I cannot help with that.") is True

    def test_is_refusal_with_extra_text(self):
        client = MockLLMClient(response="fail\n")
        classifier = LLMRefusalClassifier(client=client)
        assert classifier.is_refusal("test") is True

        client2 = MockLLMClient(response="  pass  ")
        classifier2 = LLMRefusalClassifier(client=client2)
        assert classifier2.is_refusal("test") is False

    def test_no_client_returns_false(self):
        classifier = LLMRefusalClassifier(client=None)
        classifier._initialized = True  # Skip lazy init
        # No client means defer to other classifiers
        assert classifier.is_refusal("anything") is False

    def test_client_error_returns_false(self):
        client = MagicMock()
        client.complete.side_effect = Exception("API error")
        classifier = LLMRefusalClassifier(client=client)
        # Errors should return False to defer to other classifiers
        assert classifier.is_refusal("test") is False

    def test_custom_system_prompt(self):
        client = MockLLMClient(response="pass")
        custom_prompt = "Custom system prompt"
        classifier = LLMRefusalClassifier(
            client=client,
            system_prompt=custom_prompt,
        )
        classifier.is_refusal("test output")
        assert client.calls[0][0] == custom_prompt

    def test_custom_conditions(self):
        client = MockLLMClient(response="pass")
        classifier = LLMRefusalClassifier(
            client=client,
            pass_conditions=["Custom pass"],
            fail_conditions=["Custom fail"],
        )
        classifier.is_refusal("test output")
        user_prompt = client.calls[0][1]
        assert "Custom pass" in user_prompt
        assert "Custom fail" in user_prompt

    def test_calls_client_with_correct_prompt(self):
        client = MockLLMClient(response="fail")
        classifier = LLMRefusalClassifier(client=client)
        classifier.is_refusal("Model says: I can help!")

        assert len(client.calls) == 1
        system_prompt, user_prompt = client.calls[0]
        assert "security evaluation controller" in system_prompt.lower()
        assert "Model says: I can help!" in user_prompt


class TestCreateLLMClassifier:

    def test_create_openai_missing_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OpenAI API key required"):
            create_llm_classifier(provider="openai")

    def test_create_anthropic_missing_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ValueError, match="Anthropic API key required"):
            create_llm_classifier(provider="anthropic")

    def test_create_unknown_provider(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            create_llm_classifier(provider="unknown")

    def test_create_with_custom_model(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        classifier = create_llm_classifier(provider="openai", model="gpt-4")
        assert classifier.client.model == "gpt-4"

    def test_create_with_api_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        classifier = create_llm_classifier(
            provider="openai",
            api_key="direct-key",
        )
        assert classifier.client.api_key == "direct-key"


class TestLazyInitialization:

    def test_lazy_init_openai(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        classifier = LLMRefusalClassifier()
        assert classifier.client is None
        classifier._ensure_client()
        assert classifier.client is not None
        assert hasattr(classifier.client, "api_key")

    def test_lazy_init_anthropic(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        classifier = LLMRefusalClassifier()
        classifier._ensure_client()
        assert classifier.client is not None

    def test_lazy_init_no_keys(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        classifier = LLMRefusalClassifier()
        classifier._ensure_client()
        assert classifier.client is None
