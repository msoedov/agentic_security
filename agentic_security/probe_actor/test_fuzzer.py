import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
import pytest

from agentic_security.models.schemas import Scan
from agentic_security.probe_actor.fuzzer import (
    generate_prompts,
    perform_many_shot_scan,
    perform_single_shot_scan,
    process_prompt,
    scan_router,
)


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
@patch("agentic_security.probe_data.data.prepare_prompts")
async def test_perform_many_shot_scan_probe_injection(prepare_prompts_mock):
    # Mock main and probe prompt modules
    prepare_prompts_mock.side_effect = [
        [MagicMock(dataset_name="main_module", prompts=["main_prompt1"], lazy=False)],
        [MagicMock(dataset_name="probe_module", prompts=["probe_prompt1"], lazy=False)],
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


def mock_refusal_heuristic(response_json):
    return response_json.get("is_refusal", False)


class TestProcessPrompt(unittest.IsolatedAsyncioTestCase):
    async def test_successful_response_no_refusal(self):
        mock_request_factory = Mock()
        mock_request_factory.fn = AsyncMock(
            return_value=Mock(
                status_code=200,
                text="Valid response text",
                json=Mock(return_value={"is_refusal": False}),
                request="mock_request",
            )
        )

        tokens, refusal = await process_prompt(
            request_factory=mock_request_factory,
            prompt="test prompt",
            tokens=0,
            module_name="module_a",
            refusals=[],
            errors=[],
        )

        self.assertEqual(tokens, 3)  # Tokens from "Valid response text"
        self.assertTrue(refusal)

    async def test_successful_response_with_refusal(self):
        mock_request_factory = Mock()
        mock_request_factory.fn = AsyncMock(
            return_value=Mock(
                status_code=200,
                text="Response indicating refusal",
                json=Mock(return_value={"is_refusal": True}),
                request="mock_request",
            )
        )

        refusals = []
        tokens, refusal = await process_prompt(
            request_factory=mock_request_factory,
            prompt="test prompt",
            tokens=0,
            module_name="module_a",
            refusals=refusals,
            errors=[],
        )

        self.assertEqual(tokens, 3)  # Tokens from "Response indicating refusal"
        self.assertFalse(refusal)

    async def test_http_error_response(self):
        mock_request_factory = Mock()
        mock_request_factory.fn = AsyncMock(
            return_value=Mock(
                status_code=500,
                text="Internal Server Error",
                request="mock_request",
                response=Mock(),
            )
        )

        refusals = []
        with self.assertRaises(httpx.HTTPStatusError):
            await process_prompt(
                request_factory=mock_request_factory,
                prompt="test prompt",
                tokens=0,
                module_name="module_a",
                refusals=refusals,
                errors=[],
            )

    async def test_request_error(self):
        mock_request_factory = Mock()
        mock_request_factory.fn = AsyncMock(
            side_effect=httpx.RequestError("Connection error")
        )

        errors = []
        tokens, refusal = await process_prompt(
            request_factory=mock_request_factory,
            prompt="test prompt",
            tokens=0,
            module_name="module_a",
            refusals=[],
            errors=errors,
        )

        self.assertEqual(tokens, 0)
        self.assertTrue(refusal)
        self.assertEqual(len(errors), 1)
        self.assertIn("Connection error", errors[0][2])
