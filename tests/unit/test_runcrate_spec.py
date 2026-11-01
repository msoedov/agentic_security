import json

import httpx
import pytest

from agentic_security.http_spec import LLMSpec, Modality
from agentic_security.routes._specs import LLM_SPECS


def runcrate_spec() -> LLMSpec:
    entry = next(item for item in LLM_SPECS if item["name"] == "Runcrate")
    return LLMSpec.from_string(entry["spec"])


def test_runcrate_preset_parses_to_chat_completions():
    spec = runcrate_spec()

    assert spec.method == "POST"
    assert spec.url == "https://api.runcrate.ai/v1/chat/completions"
    assert spec.headers["Authorization"] == "Bearer $RUNCRATE_API_KEY"
    assert spec.model_name == "deepseek-ai/DeepSeek-V4-Flash"
    assert spec.modality == Modality.TEXT


@pytest.mark.asyncio
async def test_runcrate_preset_probe_sends_prompt_as_user_message(monkeypatch):
    captured = {}

    async def fake_request(self, method, url, headers=None, content=None, timeout=None):
        captured.update(method=method, url=url, content=content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    response = await runcrate_spec().probe('Say "hi"')

    assert response.status_code == 200
    assert captured["method"] == "POST"
    assert captured["url"] == "https://api.runcrate.ai/v1/chat/completions"
    body = json.loads(captured["content"])
    assert body["model"] == "deepseek-ai/DeepSeek-V4-Flash"
    assert body["messages"] == [{"role": "user", "content": 'Say "hi"'}]
