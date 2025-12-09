import asyncio
import os
import random
import uuid as U
from abc import ABC, abstractmethod
from collections import deque
from typing import Deque

import numpy as np
import requests

from agentic_security.logutils import logger

AUTH_TOKEN: str = os.getenv("AS_TOKEN", "gh0-5f4a8ed2-37c6-4bd7-a0cf-7070eae8115b")


class PromptSelectionInterface(ABC):
    """Abstract base class for prompt selection strategies."""

    @abstractmethod
    def select_next_prompt(self, current_prompt: str, passed_guard: bool) -> str:
        """Selects the next prompt based on current state and guard result."""
        pass

    @abstractmethod
    def select_next_prompts(self, current_prompt: str, passed_guard: bool) -> list[str]:
        """Selects the next prompts based on current state and guard result."""
        pass

    @abstractmethod
    def update_rewards(
        self,
        previous_prompt: str,
        current_prompt: str,
        reward: float,
        passed_guard: bool,
    ) -> None:
        """Updates internal rewards based on the outcome of the last selected prompt."""
        pass


class RandomPromptSelector(PromptSelectionInterface):
    """Random prompt selector with cycle prevention using history."""

    def __init__(self, prompts: list[str], history_size: int = 300):
        if not prompts:
            raise ValueError("Prompts list cannot be empty")
        self.prompts = prompts
        self.history: Deque[str] = deque(maxlen=history_size)

    def select_next_prompts(self, current_prompt: str, passed_guard: bool) -> list[str]:
        return [self.select_next_prompt(current_prompt, passed_guard)]

    def select_next_prompt(self, current_prompt: str, passed_guard: bool) -> str:
        self.history.append(current_prompt)
        available = [p for p in self.prompts if p not in self.history]

        if not available:
            available = self.prompts
            self.history.clear()

        return random.choice(available)

    def update_rewards(
        self,
        previous_prompt: str,
        current_prompt: str,
        reward: float,
        passed_guard: bool,
    ) -> None:
        pass  # No learning in random selection


class CloudRLPromptSelector(PromptSelectionInterface):
    """Cloud-based reinforcement learning prompt selector with fallback."""

    def __init__(
        self,
        prompts: list[str],
        api_url: str,
        auth_token: str = AUTH_TOKEN,
        history_size: int = 300,
        timeout: int = 5,
        run_id: str = "",
    ):
        if not prompts:
            raise ValueError("Prompts list cannot be empty")
        self.prompts = prompts
        self.api_url = api_url
        self.headers = {"Authorization": f"Bearer {auth_token}"}
        self.timeout = timeout
        self.run_id = run_id or U.uuid4().hex

    def select_next_prompt(self, current_prompt: str, passed_guard: bool) -> list[str]:
        return self.select_next_prompts(current_prompt, passed_guard)[0]

    def select_next_prompts(self, current_prompt: str, passed_guard: bool) -> str:
        try:
            response = requests.post(
                f"{self.api_url}/rl-model/select-next-prompt",
                json={
                    "run_id": U.uuid4().hex,
                    "current_prompt": current_prompt,
                    "passed_guard": passed_guard,
                },
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json().get("next_prompts", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Cloud request failed: {e}")
            return [self._fallback_selection()]

    def _fallback_selection(self) -> str:
        return random.choice(self.prompts)

    def update_rewards(
        self,
        previous_prompt: str,
        current_prompt: str,
        reward: float,
        passed_guard: bool,
    ) -> None: ...


class QLearningPromptSelector(PromptSelectionInterface):
    """Q-Learning based prompt selector with exploration/exploitation tradeoff."""

    def __init__(
        self,
        prompts: list[str],
        learning_rate: float = 0.1,
        discount_factor: float = 0.9,
        initial_exploration: float = 1.0,
        exploration_decay: float = 0.995,
        min_exploration: float = 0.01,
        history_size: int = 300,
    ):
        if not prompts:
            raise ValueError("Prompts list cannot be empty")

        self.prompts = prompts
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = initial_exploration
        self.exploration_decay = exploration_decay
        self.min_exploration = min_exploration
        self.history: Deque[str] = deque(maxlen=history_size)

        # Initialize Q-table with small random values
        self.q_table: dict[str, dict[str, float]] = {
            state: {
                action: np.random.uniform(0, 0.1)
                for action in prompts
                if action != state
            }
            for state in prompts
        }

    def select_next_prompts(self, current_prompt: str, passed_guard: bool) -> list[str]:
        return [self.select_next_prompt(current_prompt, passed_guard)]

    def select_next_prompt(self, current_prompt: str, passed_guard: bool) -> str:
        self.history.append(current_prompt)
        available = [a for a in self.prompts if a not in self.history]

        if not available:
            available = self.prompts
            self.history.clear()

        # Exploration-exploitation tradeoff
        if np.random.random() < self.exploration_rate:
            selected = random.choice(available)
        else:
            q_values = {a: self.q_table[current_prompt][a] for a in available}
            selected = max(q_values, key=q_values.get)  # type: ignore

        # Decay exploration rate
        self.exploration_rate = max(
            self.min_exploration, self.exploration_rate * self.exploration_decay
        )
        return selected

    def update_rewards(
        self,
        previous_prompt: str,
        current_prompt: str,
        reward: float,
        passed_guard: bool,
    ) -> None:
        if (
            previous_prompt not in self.q_table
            or current_prompt not in self.q_table[previous_prompt]
        ):
            return

        # Calculate temporal difference error
        max_future_q = max(self.q_table[current_prompt].values(), default=0.0)
        td_target = reward + self.discount_factor * max_future_q
        td_error = td_target - self.q_table[previous_prompt][current_prompt]

        # Update Q-value
        self.q_table[previous_prompt][current_prompt] += self.learning_rate * td_error


class Module:
    def __init__(
        self,
        prompt_groups: list[str],
        tools_inbox: asyncio.Queue,
        opts: dict = {},
        rl_model: PromptSelectionInterface | None = None,
    ):
        self.tools_inbox = tools_inbox
        self.opts = opts
        self.prompt_groups = prompt_groups
        self.max_prompts = self.opts.get("max_prompts", 10)  # Default max M prompts
        self.run_id = U.uuid4().hex
        self.batch_size = self.opts.get("batch_size", 500)
        self.rl_model = rl_model or CloudRLPromptSelector(
            prompt_groups, "https://mcp.metaheuristic.co", run_id=self.run_id
        )

    async def apply(self):
        current_prompt = "What is AI?"
        passed_guard = False
        for _ in range(max(self.max_prompts, 1)):
            # Fetch prompts from the API
            prompts = await asyncio.to_thread(
                lambda: self.rl_model.select_next_prompts(
                    current_prompt, passed_guard=passed_guard
                )
            )

            if not prompts:
                logger.error("No prompts retrieved from the API.")
                return

            logger.info(f"Retrieved {len(prompts)} prompts.")

            for i, prompt in enumerate(prompts):
                logger.info(f"Processing prompt {i+1}/{len(prompts)}: {prompt}")
                yield prompt
                current_prompt = prompt
                while not self.tools_inbox.empty():
                    ref = await self.tools_inbox.get()
                    print(ref, "ref")
                    message, _, ready = ref["message"], ref["reply"], ref["ready"]
                    yield message
                    ready.set()
