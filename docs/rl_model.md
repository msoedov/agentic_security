# RL prompt selection

The module `agentic_security.probe_data.modules.rl_model` selects the next attack prompt. It uses the guard result and a reward to make the selection.

## Selectors

All selectors implement `PromptSelectionInterface`:

```python
select_next_prompt(current_prompt: str, passed_guard: bool) -> str
select_next_prompts(current_prompt: str, passed_guard: bool) -> list[str]
update_rewards(previous_prompt: str, current_prompt: str, reward: float, passed_guard: bool) -> None
```

### RandomPromptSelector

Selects a random prompt. It keeps a history to prevent repeated cycles.

| Argument | Default | Description |
| --- | --- | --- |
| `prompts` | – | The list of prompts. |
| `history_size` | `300` | The size of the history. |

`update_rewards` does nothing.

### QLearningPromptSelector

Selects prompts with Q-learning. The exploration rate decreases after each selection.

| Argument | Default | Description |
| --- | --- | --- |
| `prompts` | – | The list of prompts. |
| `learning_rate` | `0.1` | The learning rate. |
| `discount_factor` | `0.9` | The discount factor. |
| `initial_exploration` | `1.0` | The exploration rate at the start. |
| `exploration_decay` | `0.995` | The decrease of the exploration rate. |
| `min_exploration` | `0.01` | The minimum exploration rate. |
| `history_size` | `300` | The size of the history. |

### CloudRLPromptSelector

Gets the next prompts from a remote RL service. If the request fails, it selects a random prompt.

| Argument | Default | Description |
| --- | --- | --- |
| `prompts` | – | The list of prompts. |
| `api_url` | – | The URL of the RL service. |
| `auth_token` | `AS_TOKEN` environment variable | The token for the service. |
| `history_size` | `300` | The size of the history. |
| `timeout` | `5` | The request timeout in seconds. |
| `run_id` | random UUID | The identifier of the run. |

## Module

`Module` uses a selector in a scan.

| Argument | Description |
| --- | --- |
| `prompt_groups` | The prompts. |
| `tools_inbox` | An `asyncio.Queue` for messages. |
| `opts["max_prompts"]` | The number of selection rounds. The default is `10`. |
| `opts["batch_size"]` | The batch size. The default is `500`. |
| `rl_model` | The selector. The default is `CloudRLPromptSelector` with `https://mcp.metaheuristic.co`. |

> **WARNING:** The default selector sends your prompts to `https://mcp.metaheuristic.co`. To keep the prompts on your computer, give a local selector as `rl_model`.

```python
import asyncio

from agentic_security.probe_data.modules.rl_model import Module, QLearningPromptSelector

prompts = ["What is AI?", "Explain ML", "Describe RL"]


async def main():
    module = Module(prompts, asyncio.Queue(), rl_model=QLearningPromptSelector(prompts))
    async for prompt in module.apply():
        print(prompt)

asyncio.run(main())
```
