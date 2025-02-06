# RL Model Module

The RL Model module provides reinforcement learning-based prompt selection strategies for the probe system.

## Overview

The module implements several prompt selection strategies that use reinforcement learning techniques to optimize prompt selection based on guard results and rewards.

## Classes

### PromptSelectionInterface

Abstract base class defining the interface for prompt selection strategies.

**Methods:**

- `select_next_prompt(current_prompt: str, passed_guard: bool) -> str`
- `select_next_prompts(current_prompt: str, passed_guard: bool) -> list[str]`
- `update_rewards(previous_prompt: str, current_prompt: str, reward: float, passed_guard: bool) -> None`

### RandomPromptSelector

Basic random selection strategy with cycle prevention using history.

**Configuration:**

- `prompts`: List of available prompts
- `history_size`: Size of history buffer to prevent cycles (default: 300)

### CloudRLPromptSelector

Cloud-based reinforcement learning prompt selector with fallback to random selection.

**Configuration:**

- `prompts`: List of available prompts
- `api_url`: URL of the RL service
- `auth_token`: Authentication token (default: AS_TOKEN environment variable)
- `history_size`: Size of history buffer (default: 300)
- `timeout`: Request timeout in seconds (default: 5)
- `run_id`: Unique identifier for the run

### QLearningPromptSelector

Q-Learning based prompt selector with exploration/exploitation tradeoff.

**Configuration:**

- `prompts`: List of available prompts
- `learning_rate`: Learning rate (default: 0.1)
- `discount_factor`: Discount factor (default: 0.9)
- `initial_exploration`: Initial exploration rate (default: 1.0)
- `exploration_decay`: Exploration decay rate (default: 0.995)
- `min_exploration`: Minimum exploration rate (default: 0.01)
- `history_size`: Size of history buffer (default: 300)

### Module

Main class that implements the RL-based prompt selection functionality.

**Configuration:**

- `prompt_groups`: List of prompt groups
- `tools_inbox`: asyncio.Queue for tool communication
- `opts`: Additional options
  - `max_prompts`: Maximum number of prompts to generate (default: 10)
  - `batch_size`: Batch size for processing (default: 500)

## Usage Example

```python
from agentic_security.probe_data.modules.rl_model import (
    Module,
    CloudRLPromptSelector,
    QLearningPromptSelector
)

# Initialize with prompt groups
prompt_groups = ["What is AI?", "Explain ML", "Describe RL"]
module = Module(prompt_groups, asyncio.Queue())

# Use the module
async for prompt in module.apply():
    print(f"Selected prompt: {prompt}")
```

## API Reference

### PromptSelectionInterface

```python
class PromptSelectionInterface(ABC):
    @abstractmethod
    def select_next_prompt(self, current_prompt: str, passed_guard: bool) -> str:
        """Select next prompt based on current state and guard result."""

    @abstractmethod
    def select_next_prompts(self, current_prompt: str, passed_guard: bool) -> list[str]:
        """Select next prompts based on current state and guard result."""

    @abstractmethod
    def update_rewards(
        self,
        previous_prompt: str,
        current_prompt: str,
        reward: float,
        passed_guard: bool,
    ) -> None:
        """Update internal rewards based on outcome of last selected prompt."""
```

### RandomPromptSelector

```python
class RandomPromptSelector(PromptSelectionInterface):
    def __init__(self, prompts: list[str], history_size: int = 300):
        """Initialize with prompts and history size."""

    def select_next_prompt(self, current_prompt: str, passed_guard: bool) -> str:
        """Select next prompt randomly with cycle prevention."""

    def update_rewards(
        self,
        previous_prompt: str,
        current_prompt: str,
        reward: float,
        passed_guard: bool,
    ) -> None:
        """No learning in random selection."""
```

### CloudRLPromptSelector

```python
class CloudRLPromptSelector(PromptSelectionInterface):
    def __init__(
        self,
        prompts: list[str],
        api_url: str,
        auth_token: str = AUTH_TOKEN,
        history_size: int = 300,
        timeout: int = 5,
        run_id: str = "",
    ):
        """Initialize with cloud RL configuration."""

    def select_next_prompts(self, current_prompt: str, passed_guard: bool) -> list[str]:
        """Select next prompts using cloud RL with fallback."""

    def _fallback_selection(self) -> str:
        """Fallback to random selection if cloud request fails."""
```

### QLearningPromptSelector

```python
class QLearningPromptSelector(PromptSelectionInterface):
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
        """Initialize Q-Learning configuration."""

    def select_next_prompt(self, current_prompt: str, passed_guard: bool) -> str:
        """Select next prompt using Q-Learning with exploration/exploitation."""

    def update_rewards(
        self,
        previous_prompt: str,
        current_prompt: str,
        reward: float,
        passed_guard: bool,
    ) -> None:
        """Update Q-values based on reward."""
```

### Module

```python
class Module:
    def __init__(
        self, prompt_groups: list[str], tools_inbox: asyncio.Queue, opts: dict = {}
    ):
        """Initialize module with prompt groups and configuration."""

    async def apply(self):
        """Apply the RL model to generate prompts."""
```
