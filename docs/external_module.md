# External modules

A module makes attack prompts from an external tool or service. The modules are in `agentic_security.probe_data.modules`.

## Built-in modules

| Module | Source |
| --- | --- |
| `garak_tool` | [Garak](https://github.com/leondz/garak) |
| `inspect_ai_tool` | [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) |
| `adaptive_attacks` | [llm-adaptive-attacks](https://github.com/tml-epfl/llm-adaptive-attacks) |
| `fine_tuned` | Gets prompts from a remote attacker API |
| `rl_model` | Reinforcement-learning prompt selection |

## Interface

Each module is a class with the name `Module`.

```python
class Module:
    def __init__(self, prompt_groups: list, tools_inbox: asyncio.Queue, opts: dict = {}): ...
    def apply(self): ...
```

- `prompt_groups` is the input for the module.
- `tools_inbox` is a queue. The module can put messages in it.
- `opts` is a dictionary with options for the module. If you do not give `opts`, the module uses `{}`.
- `apply()` yields prompts. Most modules use an async generator. `adaptive_attacks` uses a sync generator.

`ModuleProtocol` in `probe_data.modules.module_protocol` is the type for this interface.

## Example

```python
import asyncio

from agentic_security.probe_data.modules.garak_tool import Module as GarakModule


async def main():
    module = GarakModule(["group_a"], asyncio.Queue(), {"port": 8718})
    async for result in module.apply():
        print(result)

asyncio.run(main())
```

## Make a custom module

```python
import asyncio


class Module:
    def __init__(self, prompt_groups: list, tools_inbox: asyncio.Queue, opts: dict | None = None):
        self.prompt_groups = prompt_groups
        self.tools_inbox = tools_inbox
        self.opts = opts or {}

    async def apply(self):
        for group in self.prompt_groups:
            prompt = f"processed {group}"
            await self.tools_inbox.put({"message": prompt})
            yield prompt
```
