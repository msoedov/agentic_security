# Module interface

Probe data modules in `agentic_security.probe_data.modules` share the same
constructor arguments. `apply` yields result strings; some modules implement
it as a sync iterator and others as an async iterator.

Built-in examples:

- `agentic_security.probe_data.modules.garak_tool`
- `agentic_security.probe_data.modules.fine_tuned`
- `agentic_security.probe_data.modules.inspect_ai_tool`
- `agentic_security.probe_data.modules.rl_model`

## Constructor

```python
def __init__(
    self,
    prompt_groups: list,
    tools_inbox: asyncio.Queue,
    opts: dict | None = None,
): ...
```

`opts` is a module-specific dictionary. An omitted `opts` is treated as `{}`.

## Usage

```python
import asyncio
from agentic_security.probe_data.modules.garak_tool import Module as GarakModule

tools_inbox = asyncio.Queue()
module = GarakModule(["group_a"], tools_inbox, {"port": 8718})

async def main():
    async for result in module.apply():
        print(result)

asyncio.run(main())
```

## Custom module

```python
import asyncio


class MyModule:
    def __init__(self, prompt_groups, tools_inbox, opts=None):
        self.prompt_groups = prompt_groups
        self.tools_inbox = tools_inbox
        self.opts = opts or {}

    async def apply(self):
        for group in self.prompt_groups:
            result = f"processed {group}"
            await self.tools_inbox.put({"message": result})
            yield result
```
