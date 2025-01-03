import asyncio

import pytest

from agentic_security.probe_data.modules.fine_tuned import Module


@pytest.mark.asyncio
async def test_module_initialization():
    tools_inbox = asyncio.Queue()
    prompt_groups = ["group1", "group2"]
    opts = {"max_prompts": 1000, "batch_size": 100}
    module = Module(prompt_groups, tools_inbox, opts)

    assert module.max_prompts == 1000
    assert module.batch_size == 100
    assert module.run_id is not None


@pytest.mark.asyncio
async def test_fetch_prompts(mocker):
    tools_inbox = asyncio.Queue()
    prompt_groups = ["group1", "group2"]
    module = Module(prompt_groups, tools_inbox)

    mocker.patch(
        "agentic_security.probe_data.modules.fine_tuned.httpx.AsyncClient.post",
        return_value=mocker.Mock(
            status_code=200, json=lambda: {"prompts": ["prompt1", "prompt2"]}
        ),
    )

    prompts = await module.fetch_prompts()
    assert prompts == ["prompt1", "prompt2"]


@pytest.mark.asyncio
async def test_post_prompt(mocker):
    tools_inbox = asyncio.Queue()
    prompt_groups = ["group1", "group2"]
    module = Module(prompt_groups, tools_inbox)

    mocker.patch(
        "agentic_security.probe_data.modules.fine_tuned.httpx.AsyncClient.post",
        return_value=mocker.Mock(status_code=200, json=lambda: {"response": "success"}),
    )

    response = await module.post_prompt("test prompt")
    assert response == {"response": "success"}


@pytest.mark.asyncio
async def test_apply(mocker):
    tools_inbox = asyncio.Queue()
    prompt_groups = ["group1", "group2"]
    module = Module(prompt_groups, tools_inbox, {"max_prompts": 2, "batch_size": 1})

    mocker.patch(
        "agentic_security.probe_data.modules.fine_tuned.Module.fetch_prompts",
        return_value=["prompt1", "prompt2"],
    )
    mocker.patch(
        "agentic_security.probe_data.modules.fine_tuned.Module.post_prompt",
        return_value={"response": "success"},
    )

    prompts = [prompt async for prompt in module.apply()]
    # Adjust the assertion to account for batched processing
    expected_prompts = ["prompt1", "prompt2", "prompt1", "prompt2"]
    assert prompts == expected_prompts
