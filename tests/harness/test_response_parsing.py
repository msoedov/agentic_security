import json

import httpx
import pytest

from agentic_security_harness.deciders import Decision, JevDecider
from agentic_security_harness.loop import extract_response


def _json_response(payload):
    return httpx.Response(
        200,
        content=json.dumps(payload),
        headers={"content-type": "application/json"},
        request=httpx.Request("POST", "http://localhost"),
    )


@pytest.mark.parametrize("usage", [None, "unavailable", [], {"cost": None}])
def test_extract_response_handles_null_or_non_dict_usage(usage):
    text, cost = extract_response(
        _json_response(
            {
                "choices": [{"message": {"content": "I cannot help with that."}}],
                "usage": usage,
            }
        )
    )
    assert text == "I cannot help with that."
    assert cost is None

    text, cost = extract_response(
        _json_response({"response": "Refused.", "usage": usage})
    )
    assert text == "Refused."
    assert cost is None


@pytest.mark.parametrize(
    "payload",
    [
        {"choices": []},
        {"choices": None},
        {"choices": "invalid"},
        {"choices": [None]},
        {"choices": [{}]},
        {"choices": [{"message": None}]},
        {"choices": [{"message": {"content": None}}]},
    ],
)
def test_extract_response_rejects_empty_or_malformed_choices(payload):
    with pytest.raises(ValueError):
        extract_response(_json_response(payload))


def test_extract_response_reads_openai_refusal_field():
    # OpenAI returns content: null and the refusal text in `refusal`; that is a
    # refusal to classify, not a malformed response.
    text, cost = extract_response(
        _json_response(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "refusal": "I'm sorry, I can't help with that.",
                        }
                    }
                ]
            }
        )
    )
    assert text == "I'm sorry, I can't help with that."
    assert cost is None


def test_extract_response_joins_text_content_parts():
    text, _ = extract_response(
        _json_response(
            {
                "choices": [
                    {
                        "message": {
                            "content": [
                                {"type": "text", "text": "I cannot "},
                                {"type": "image_url", "image_url": {"url": "x"}},
                                {"type": "output_text", "text": "help with that."},
                            ]
                        }
                    }
                ]
            }
        )
    )
    assert text == "I cannot help with that."


@pytest.mark.parametrize(
    "message",
    [
        {"content": None, "refusal": None},
        {"content": None, "refusal": "   "},
        {"content": None, "refusal": 42},
        {"content": [], "refusal": None},
        {"content": [{"type": "image_url", "image_url": {"url": "x"}}]},
        {"content": [{"type": "text", "text": None}]},
        {"content": 42},
    ],
)
def test_extract_response_still_rejects_messages_without_text(message):
    with pytest.raises(ValueError):
        extract_response(_json_response({"choices": [{"message": message}]}))


@pytest.mark.parametrize(
    ("usage", "expected_cost"),
    [
        (None, 0.0),
        ("unavailable", 0.0),
        ({"cost": None}, 0.0),
        ({"cost": 0.005}, 0.005),
    ],
)
def test_jev_decider_handles_null_or_non_dict_usage(monkeypatch, usage, expected_cost):
    payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {"action": "escalate", "reason": "try converter"}
                    )
                }
            }
        ],
        "usage": usage,
    }
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-fake")
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: _json_response(payload))
    decision = JevDecider("test/model").decide({"allowed_actions": ["escalate"]})
    assert decision == Decision("escalate", "try converter", expected_cost)


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"choices": []},
        {"choices": None},
        {"choices": [None]},
        {"choices": [{}]},
        {"choices": [{"message": None}]},
        {"choices": [{"message": {"content": None}}]},
        {"choices": [{"message": {"content": "[]"}}]},
        {"choices": [{"message": {"content": "{}"}}]},
    ],
)
def test_jev_decider_rejects_empty_or_malformed_choices(monkeypatch, payload):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-fake")
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: _json_response(payload))
    with pytest.raises(ValueError):
        JevDecider("test/model").decide({"allowed_actions": ["stop"]})
