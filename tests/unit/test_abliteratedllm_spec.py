import json

import httpx
import pytest

from agentic_security.http_spec import LLMSpec, Modality
from agentic_security.routes._specs import LLM_SPECS


def abliteratedllm_spec() -> LLMSpec:
    entry = next(item for item in LLM_SPECS if item["name"] == "AbliteratedLLM")
    return LLMSpec.from_string(entry["spec"])


def test_abliteratedllm_preset_parses_to_chat_completions():
    spec = abliteratedllm_spec()

    assert spec.method == "POST"
    assert spec.url == "https://api.abliteratedllm.dev/v1/chat/completions"
    assert spec.headers["Authorization"] == "Bearer $ABLITERATEDLLM_API_KEY"
    assert spec.model_name == "glm-5.3-cyber-abliterated"
    assert spec.modality == Modality.TEXT


@pytest.mark.asyncio
async def test_abliteratedllm_preset_probe_sends_prompt_as_user_message(monkeypatch):
    captured = {}

    async def fake_request(self, method, url, headers=None, content=None, timeout=None):
        captured.update(method=method, url=url, content=content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    response = await abliteratedllm_spec().probe('Say "hi"')

    assert response.status_code == 200
    assert captured["method"] == "POST"
    assert captured["url"] == "https://api.abliteratedllm.dev/v1/chat/completions"
    body = json.loads(captured["content"])
    assert body["model"] == "glm-5.3-cyber-abliterated"
    assert body["messages"] == [{"role": "user", "content": 'Say "hi"'}]
