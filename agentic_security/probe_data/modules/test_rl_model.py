import asyncio
from collections import deque
from unittest.mock import Mock, patch

import numpy as np
import pytest
import requests

# Import the classes to be tested
from agentic_security.probe_data.modules.rl_model import (
    CloudRLPromptSelector,
    Module,
    QLearningPromptSelector,
    RandomPromptSelector,
)


# Fixtures for reusable test data
@pytest.fixture
def dataset_prompts() -> list[str]:
    return [
        "What is AI?",
        "How does RL work?",
        "Explain supervised learning.",
        "What is reinforcement learning?",
    ]


@pytest.fixture
def mock_requests() -> Mock:
    with patch("requests.post") as mock_requests:
        yield mock_requests


@pytest.fixture
def mock_rl_selector() -> Mock:
    return CloudRLPromptSelector(
        dataset_prompts,
        api_url="https://edge.metaheuristic.co",
    )


@pytest.fixture
def tools_inbox() -> asyncio.Queue:
    return asyncio.Queue()


# Tests for RandomPromptSelector
class TestRandomPromptSelector:
    def test_initialization(self, dataset_prompts):
        selector = RandomPromptSelector(dataset_prompts)
        assert selector.prompts == dataset_prompts
        assert isinstance(selector.history, deque)
        assert selector.history.maxlen == 3

    def test_select_next_prompt(self, dataset_prompts):
        selector = RandomPromptSelector(dataset_prompts)
        current_prompt = "What is AI?"
        next_prompt = selector.select_next_prompt(current_prompt, passed_guard=True)
        assert next_prompt in dataset_prompts
        assert next_prompt != current_prompt

    def test_update_rewards_no_op(self, dataset_prompts):
        selector = RandomPromptSelector(dataset_prompts)
        selector.update_rewards("What is AI?", "How does RL work?", 1.0, True)
        assert len(selector.history) == 0


# Tests for CloudRLPromptSelector
class TestCloudRLPromptSelector:
    def test_initialization(self, dataset_prompts):
        selector = CloudRLPromptSelector(dataset_prompts, "http://example.com", "token")
        assert selector.prompts == dataset_prompts
        assert selector.api_url == "http://example.com"
        assert selector.headers == {"Authorization": "Bearer token"}

    def test_select_next_prompt_success(self, dataset_prompts, mock_requests):
        mock_requests.return_value.status_code = 200
        mock_requests.return_value.json.return_value = {"next_prompts": ["What is AI?"]}

        selector = CloudRLPromptSelector(dataset_prompts, "http://example.com", "token")
        next_prompt = selector.select_next_prompt(
            "How does RL work?", passed_guard=True
        )
        assert next_prompt == "What is AI?"
        mock_requests.assert_called_once()

    def test_fallback_on_failure(self, dataset_prompts, mock_requests):
        mock_requests.side_effect = requests.exceptions.RequestException
        selector = CloudRLPromptSelector(dataset_prompts, "http://example.com", "token")
        next_prompt = selector.select_next_prompt("What is AI?", passed_guard=True)
        assert next_prompt in dataset_prompts

    def test_select_next_prompt_success_service(self, dataset_prompts):
        selector = CloudRLPromptSelector(
            dataset_prompts,
            api_url="https://edge.metaheuristic.co",
        )
        next_prompt = selector.select_next_prompt(
            "How does RL work?", passed_guard=True
        )
        assert next_prompt


# Tests for QLearningPromptSelector
class TestQLearningPromptSelector:
    def test_initialization(self, dataset_prompts):
        selector = QLearningPromptSelector(dataset_prompts)
        assert selector.prompts == dataset_prompts
        assert selector.exploration_rate == 1.0
        assert len(selector.q_table) == len(dataset_prompts)
        assert all(
            len(v) == len(dataset_prompts) - 1 for v in selector.q_table.values()
        )

    def test_select_next_prompt_exploration(self, dataset_prompts):
        selector = QLearningPromptSelector(dataset_prompts, initial_exploration=1.0)
        next_prompt = selector.select_next_prompt("What is AI?", passed_guard=True)
        assert next_prompt in dataset_prompts
        assert next_prompt != "What is AI?"

    def test_select_next_prompt_exploitation(self, dataset_prompts):
        selector = QLearningPromptSelector(dataset_prompts, initial_exploration=0.0)
        selector.q_table["What is AI?"]["How does RL work?"] = 10.0
        next_prompt = selector.select_next_prompt("What is AI?", passed_guard=True)
        assert next_prompt == "How does RL work?"

    def test_update_rewards(self, dataset_prompts):
        selector = QLearningPromptSelector(dataset_prompts)
        selector.update_rewards("What is AI?", "How does RL work?", 1.0, True)
        assert selector.q_table["What is AI?"]["How does RL work?"] > 0.0

    def test_exploration_rate_decay(self, dataset_prompts):
        selector = QLearningPromptSelector(
            dataset_prompts, initial_exploration=1.0, exploration_decay=0.9
        )
        assert selector.exploration_rate == 1.0
        selector.select_next_prompt("What is AI?", passed_guard=True)
        assert selector.exploration_rate == 0.9
        selector.select_next_prompt("How does RL work?", passed_guard=True)
        assert selector.exploration_rate == 0.81


# Edge Cases and Error Handling
def test_empty_prompts():
    with pytest.raises(ValueError, match="Prompts list cannot be empty"):
        RandomPromptSelector([])


def test_cloud_rl_selector_invalid_url(dataset_prompts):
    selector = CloudRLPromptSelector(dataset_prompts, "invalid_url", "token")
    next_prompt = selector.select_next_prompt("What is AI?", passed_guard=True)
    assert next_prompt in dataset_prompts


def test_q_learning_selector_invalid_reward(dataset_prompts):
    selector = QLearningPromptSelector(dataset_prompts)
    selector.update_rewards("What is AI?", "How does RL work?", np.nan, True)


# Tests for Module class
class TestModule:
    @pytest.fixture
    def mock_uuid(self):
        with patch("uuid.uuid4") as mock:
            mock.return_value.hex = "test_run_id"
            yield mock

    def test_initialization(self, dataset_prompts, tools_inbox, mock_uuid):
        module = Module(dataset_prompts, tools_inbox)
        assert module.prompt_groups == dataset_prompts
        assert module.tools_inbox == tools_inbox
        assert module.max_prompts == 2000
        assert module.batch_size == 500
        assert module.run_id == "test_run_id"
        assert isinstance(module.rl_model, CloudRLPromptSelector)

    def test_initialization_with_options(self, dataset_prompts, tools_inbox, mock_uuid):
        opts = {
            "max_prompts": 100,
            "batch_size": 50,
        }
        module = Module(dataset_prompts, tools_inbox, opts)
        assert module.max_prompts == 100
        assert module.batch_size == 50

    @pytest.mark.asyncio
    async def test_apply_basic_flow(
        self, dataset_prompts, tools_inbox, mock_rl_selector
    ):
        module = Module(dataset_prompts, tools_inbox)

        count = 0
        async for prompt in module.apply():
            assert prompt == "Test prompt"
            count += 1
            if count >= 3:  # Test a few iterations
                break

    @pytest.mark.asyncio
    async def test_apply_rl_with_tools_inbox(self, dataset_prompts, tools_inbox):
        # Add a test message to the tools inbox
        test_message = {
            "message": "Test message",
            "reply": None,
            "ready": asyncio.Event(),
        }
        await tools_inbox.put(test_message)

        module = Module(dataset_prompts, tools_inbox)

        async for output in module.apply():
            if output == "Test message":
                test_message["ready"].set()
                break
