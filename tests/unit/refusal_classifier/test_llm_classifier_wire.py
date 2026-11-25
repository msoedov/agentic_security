"""The judge clients, driven through the real SDKs against a localhost fake.

No network and no credentials: tests/fakes/fake_llm_api.py answers the
OpenAI and Anthropic routes and records header names only.
"""

from agentic_security.refusal_classifier.llm_classifier import (
    AnthropicClient,
    LLMRefusalClassifier,
    OpenAIClient,
)
from agentic_security.refusal_classifier.untrusted import TAG

KEY = "sk-test-wire-0123456789"


def test_openai_judge_over_the_wire(fake_llm_api):
    fake_llm_api.reply = "pass"
    client = OpenAIClient(api_key=KEY, base_url=fake_llm_api.url + "/v1")
    classifier = LLMRefusalClassifier(client=client)

    assert classifier.is_refusal("Sure, here is how.") is False

    (body,) = fake_llm_api.bodies("/chat/completions")
    user = next(m["content"] for m in body["messages"] if m["role"] == "user")
    assert f"<{TAG}>\nSure, here is how.\n</{TAG}>" in user
    assert body["temperature"] == 0


def test_anthropic_judge_over_the_wire(fake_llm_api, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_BASE_URL", fake_llm_api.url)
    fake_llm_api.reply = "fail"
    classifier = LLMRefusalClassifier(client=AnthropicClient(api_key=KEY))

    assert classifier.is_refusal("I can't help with that.") is True

    (body,) = fake_llm_api.bodies("/messages")
    assert body["model"] == "claude-haiku-5-5"
    assert "security evaluation controller" in body["system"].lower()


def test_fake_never_records_header_values(fake_llm_api):
    OpenAIClient(api_key=KEY, base_url=fake_llm_api.url + "/v1").complete("s", "u")
    (request,) = fake_llm_api.requests
    assert "authorization" in request["headers"]
    assert KEY not in repr(fake_llm_api.requests)
