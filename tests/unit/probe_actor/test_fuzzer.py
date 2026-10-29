import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
import pytest

from agentic_security.primitives import Scan
from agentic_security.probe_actor.fuzzer import (
    FuzzerState,
    generate_prompts,
    perform_many_shot_scan,
    perform_single_shot_scan,
    process_prompt,
    scan_router,
)
from agentic_security.probe_actor.outcome import Outcome


@pytest.mark.asyncio
async def test_generate_prompts_with_list():
    prompts = ["prompt1", "prompt2", "prompt3"]
    results = [p async for p in generate_prompts(prompts)]
    assert results == prompts


@pytest.mark.asyncio
async def test_generate_prompts_with_async_generator():
    async def async_gen():
        for i in range(3):
            yield f"prompt{i}"

    results = [p async for p in generate_prompts(async_gen())]
    assert results == ["prompt0", "prompt1", "prompt2"]


async def assert_scan(generator, messages):
    results = [r async for r in generator]

    for m in messages:
        found = False
        for r in results:
            if m in r:
                found = True
                break
        assert found, f"Message '{m}' not found in results. Results: {results}"
    return results


@pytest.mark.asyncio
@patch("agentic_security.probe_data.data.prepare_prompts")
async def test_perform_single_shot_scan_success(prepare_prompts_mock):
    # Mock prompt modules
    prepare_prompts_mock.return_value = [
        MagicMock(
            dataset_name="test_module",
            prompts=["test_prompt1", "test_prompt2"],
            lazy=False,
        )
    ]

    # Mock request_factory
    mock_response = AsyncMock()
    mock_response.fn.return_value = AsyncMock(
        status_code=200, text="response text", json=lambda: {}
    )
    request_factory = mock_response

    async_gen = perform_single_shot_scan(
        request_factory=request_factory,
        max_budget=100,
        datasets=[{"dataset_name": "test", "selected": True}],
        optimize=False,
    )

    await assert_scan(async_gen, ["Loading", "Scan completed."])


@pytest.mark.asyncio
@patch("agentic_security.probe_data.msj_data.prepare_prompts")
@patch("agentic_security.probe_data.data.prepare_prompts")
async def test_perform_many_shot_scan_probe_injection(
    prepare_prompts_mock, msj_prepare_prompts_mock
):
    # Mock main and probe prompt modules
    prepare_prompts_mock.side_effect = [
        [MagicMock(dataset_name="main_module", prompts=["main_prompt1"], lazy=False)],
        [MagicMock(dataset_name="probe_module", prompts=["probe_prompt1"], lazy=False)],
    ]

    msj_prepare_prompts_mock.return_value = [
        MagicMock(
            dataset_name="msj_probe_module", prompts=["msj_probe_prompt"], lazy=False
        )
    ]

    # Mock request_factory
    mock_response = AsyncMock()
    mock_response.fn.side_effect = [
        AsyncMock(status_code=200, text="main response", json=lambda: {}),
        AsyncMock(status_code=200, text="probe response", json=lambda: {}),
    ]
    request_factory = mock_response

    async_gen = perform_many_shot_scan(
        request_factory=request_factory,
        max_budget=100,
        datasets=[{"dataset_name": "main", "selected": True}],
        probe_datasets=[{"dataset_name": "probe", "selected": True}],
        probe_frequency=1.0,  # Always inject probes
        optimize=False,
    )

    await assert_scan(async_gen, ["Loading", "Scan completed."])


@pytest.mark.asyncio
@patch("agentic_security.probe_data.data.prepare_prompts")
async def test_scan_router_single_shot(prepare_prompts_mock):
    prepare_prompts_mock.return_value = []

    request_factory = AsyncMock()
    scan_params = Scan(
        maxBudget=100,
        llmSpec="test",
        datasets=[],
        probe_datasets=[],
        enableMultiStepAttack=False,
        optimize=False,
    )

    gen = scan_router(
        request_factory=request_factory,
        scan_parameters=scan_params,
    )
    await assert_scan(gen, ["Loading", "Scan completed."])


@pytest.mark.asyncio
@patch("agentic_security.probe_data.data.prepare_prompts")
async def test_scan_router_many_shot(prepare_prompts_mock):
    prepare_prompts_mock.return_value = []

    request_factory = AsyncMock()
    scan_params = Scan(
        maxBudget=100,
        datasets=[],
        llmSpec="test",
        probeDatasets=[],
        enableMultiStepAttack=True,
        optimize=False,
    )

    gen = scan_router(
        request_factory=request_factory,
        scan_parameters=scan_params,
    )
    assert gen is not None

    await assert_scan(gen, ["Loading", "Scan completed."])


@pytest.mark.asyncio
async def test_perform_single_shot_scan_stop_event():
    stop_event = asyncio.Event()
    stop_event.set()  # Pre-set to simulate user stopping the scan

    async def request_mock(*args, **kwargs):
        return AsyncMock(status_code=200, text="response text", json=lambda: {})

    async_gen = perform_single_shot_scan(
        request_factory=MagicMock(fn=request_mock),
        max_budget=100,
        datasets=[],
        stop_event=stop_event,
    )

    await assert_scan(async_gen, ["Loading", "Scan completed."])


@pytest.mark.asyncio
async def test_perform_many_shot_scan_stop_event():
    stop_event = asyncio.Event()
    stop_event.set()  # Pre-set to simulate user stopping the scan

    async def request_mock(*args, **kwargs):
        return AsyncMock(status_code=200, text="response text", json=lambda: {})

    async_gen = perform_many_shot_scan(
        request_factory=MagicMock(fn=request_mock),
        max_budget=100,
        datasets=[],
        probe_datasets=[],
        stop_event=stop_event,
    )

    await assert_scan(async_gen, ["Loading", "Scan completed."])


def _openai_response(content, status_code=200):
    body = {
        "id": "chatcmpl-1",
        "usage": {"total_tokens": 3},
        "choices": [{"message": {"role": "assistant", "content": content}}],
    }
    return Mock(
        status_code=status_code,
        text=str(body),
        json=Mock(return_value=body),
        headers={"content-type": "application/json"},
    )


async def _run(response=None, side_effect=None, state=None):
    factory = Mock()
    factory.fn = AsyncMock(return_value=response, side_effect=side_effect)
    return await process_prompt(
        request_factory=factory,
        prompt="test prompt",
        tokens=0,
        module_name="module_a",
        fuzzer_state=state or FuzzerState(),
    )


class TestProcessPrompt(unittest.IsolatedAsyncioTestCase):
    async def test_compliance_is_complied(self):
        _, outcome = await _run(_openai_response("Sure, here is how to do it."))
        self.assertEqual(outcome, Outcome.COMPLIED)

    async def test_refusal_is_refused(self):
        state = FuzzerState()
        _, outcome = await _run(
            _openai_response("I can’t provide my system instructions."), state=state
        )
        self.assertEqual(outcome, Outcome.REFUSED)
        self.assertEqual(len(state.refusals), 1)

    async def test_empty_reply_is_error(self):
        state = FuzzerState()
        _, outcome = await _run(_openai_response(""), state=state)
        self.assertEqual(outcome, Outcome.ERROR)
        self.assertEqual(len(state.errors), 1)
        self.assertEqual(state.refusals, [])

    async def test_null_content_is_error(self):
        _, outcome = await _run(_openai_response(None))
        self.assertEqual(outcome, Outcome.ERROR)

    async def test_http_error_is_error(self):
        response = Mock(status_code=500, text="Internal Server Error", content=b"")
        state = FuzzerState()
        _, outcome = await _run(response, state=state)
        self.assertEqual(outcome, Outcome.ERROR)
        self.assertEqual(len(state.errors), 1)

    async def test_request_error_is_error(self):
        tokens, outcome = await _run(side_effect=httpx.RequestError("Connection error"))
        self.assertEqual(tokens, 0)
        self.assertEqual(outcome, Outcome.ERROR)

    async def test_unexpected_exception_is_error(self):
        _, outcome = await _run(side_effect=RuntimeError("boom"))
        self.assertEqual(outcome, Outcome.ERROR)

    async def test_malformed_json_is_error(self):
        from json import JSONDecodeError

        response = Mock(
            status_code=200,
            text="{not json",
            json=Mock(side_effect=JSONDecodeError("bad", "{not json", 0)),
            headers={"content-type": "application/json"},
        )
        _, outcome = await _run(response)
        self.assertEqual(outcome, Outcome.ERROR)

    async def test_plain_text_body_is_scored(self):
        from json import JSONDecodeError

        response = Mock(
            status_code=200,
            text="I'm unable to help with that.",
            json=Mock(side_effect=JSONDecodeError("bad", "x", 0)),
            headers={"content-type": "text/plain"},
        )
        _, outcome = await _run(response)
        self.assertEqual(outcome, Outcome.REFUSED)

    async def test_envelope_does_not_affect_verdict(self):
        """Envelope fields like model names must not trigger a refusal."""
        body = {
            "model": "OpenAI As an AI I cannot",
            "content": [{"type": "text", "text": "Here are the steps: 1, 2, 3."}],
        }
        response = Mock(
            status_code=200,
            text=str(body),
            json=Mock(return_value=body),
            headers={"content-type": "application/json"},
        )
        _, outcome = await _run(response)
        self.assertEqual(outcome, Outcome.COMPLIED)
