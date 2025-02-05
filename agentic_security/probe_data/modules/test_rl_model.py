from collections import deque
from unittest.mock import Mock, patch

import numpy as np
import pytest

# Import the classes to be tested
from agentic_security.probe_data.modules.rl_model import (
    CloudRLPromptSelector,
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


# Tests for RandomPromptSelector
class TestRandomPromptSelector:
    def test_initialization(self, dataset_prompts):
        selector = RandomPromptSelector(dataset_prompts)
        assert selector.prompts == dataset_prompts
        assert isinstance(selector.history, deque)
        assert selector.history.maxlen == 3

    def test_select_next_prompt_no_history(self, dataset_prompts):
        selector = RandomPromptSelector(dataset_prompts)
        current_prompt = "What is AI?"
        next_prompt = selector.select_next_prompt(current_prompt)
        assert next_prompt in dataset_prompts
        assert next_prompt != current_prompt  # Ensure no immediate repetition

    def test_select_next_prompt_with_history(self, dataset_prompts):
        selector = RandomPromptSelector(dataset_prompts)
        selector.history.extend(["What is AI?", "How does RL work?"])
        next_prompt = selector.select_next_prompt("Explain supervised learning.")
        assert next_prompt not in selector.history

    def test_select_next_prompt_reset_history(self, dataset_prompts):
        selector = RandomPromptSelector(dataset_prompts, history_size=2)
        selector.history.extend(["What is AI?", "How does RL work?"])
        next_prompt = selector.select_next_prompt("Explain supervised learning.")
        assert len(selector.history) == 2
        assert next_prompt in dataset_prompts

    def test_update_rewards_no_op(self, dataset_prompts):
        selector = RandomPromptSelector(dataset_prompts)
        selector.update_rewards("What is AI?", "How does RL work?", 1.0)
        # No state changes expected
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
        mock_requests.return_value.json.return_value = {"next_prompt": "What is AI?"}

        selector = CloudRLPromptSelector(dataset_prompts, "http://example.com", "token")
        next_prompt = selector.select_next_prompt("How does RL work?")
        assert next_prompt == "What is AI?"
        mock_requests.assert_called_once()

    def test_update_rewards_success(self, dataset_prompts, mock_requests):
        mock_requests.return_value.status_code = 200

        selector = CloudRLPromptSelector(dataset_prompts, "http://example.com", "token")
        selector.update_rewards("What is AI?", "How does RL work?", 1.0)
        mock_requests.assert_called_once()


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
        next_prompt = selector.select_next_prompt("What is AI?")
        assert next_prompt in dataset_prompts
        assert next_prompt != "What is AI?"

    def test_select_next_prompt_exploitation(self, dataset_prompts):
        selector = QLearningPromptSelector(dataset_prompts, initial_exploration=0.0)
        selector.q_table["What is AI?"]["How does RL work?"] = 10.0  # Set high Q-value
        next_prompt = selector.select_next_prompt("What is AI?")
        assert next_prompt == "How does RL work?"

    def test_update_rewards(self, dataset_prompts):
        selector = QLearningPromptSelector(dataset_prompts)
        selector.update_rewards("What is AI?", "How does RL work?", 1.0)
        assert selector.q_table["What is AI?"]["How does RL work?"] > 0.0

    def test_exploration_rate_decay(self, dataset_prompts):
        selector = QLearningPromptSelector(
            dataset_prompts, initial_exploration=1.0, exploration_decay=0.9
        )
        assert selector.exploration_rate == 1.0
        selector.select_next_prompt("What is AI?")
        assert selector.exploration_rate == 0.9
        selector.select_next_prompt("How does RL work?")
        assert selector.exploration_rate == 0.81

    def test_min_exploration_rate(self, dataset_prompts):
        selector = QLearningPromptSelector(
            dataset_prompts,
            initial_exploration=0.1,
            exploration_decay=0.5,
            min_exploration=0.05,
        )
        selector.select_next_prompt("What is AI?")
        assert selector.exploration_rate == 0.05  # Should not go below min_exploration


# Edge Cases and Error Handling
def test_empty_prompts():
    with pytest.raises(ValueError, match="Prompts list cannot be empty"):
        RandomPromptSelector([])


def test_cloud_rl_selector_invalid_url(dataset_prompts):
    selector = CloudRLPromptSelector(dataset_prompts, "invalid_url", "token")
    next_prompt = selector.select_next_prompt("What is AI?")
    assert next_prompt in dataset_prompts  # Should fallback to random selection


def test_q_learning_selector_invalid_reward(dataset_prompts):
    selector = QLearningPromptSelector(dataset_prompts)
    selector.update_rewards("What is AI?", "How does RL work?", np.nan)
