# Dynamic module interface

Dynamic modules extend Agentic Security with prompt generators that can call external tools, adapt existing datasets, or stream prompts from another service.

## Contract

The importable contract lives at:

```python
from agentic_security.probe_data.modules import ModuleProtocol
```

A module instance exposes three attributes:

- `prompt_groups`: the configured prompt groups or datasets supplied by the registry.
- `tools_inbox`: an `asyncio.Queue` used to exchange messages with external tools.
- `opts`: module-specific configuration.

It also implements `apply()`, which yields prompt strings. Existing modules use both synchronous and asynchronous generators, so the protocol accepts either form.

```python
import asyncio
from collections.abc import Iterator
from typing import Any

from agentic_security.probe_data.modules import ModuleProtocol


class PrefixModule:
    def __init__(
        self,
        prompt_groups: list[Any],
        tools_inbox: asyncio.Queue[Any],
        opts: dict[str, Any] | None = None,
    ) -> None:
        self.prompt_groups = prompt_groups
        self.tools_inbox = tools_inbox
        self.opts = opts or {}

    def apply(self) -> Iterator[str]:
        prefix = str(self.opts.get("prefix", "Probe:"))
        for group in self.prompt_groups:
            yield f"{prefix} {group}"


module: ModuleProtocol = PrefixModule(
    prompt_groups=["hello", "world"],
    tools_inbox=asyncio.Queue(),
    opts={"prefix": "Test:"},
)
```

An asynchronous implementation can use an async generator instead:

```python
from collections.abc import AsyncIterator


async def apply(self) -> AsyncIterator[str]:
    for prompt in self.prompt_groups:
        yield str(prompt)
```

## Registration

After implementing a module, import it in `agentic_security/probe_data/data.py` and add a registry factory that constructs the module and passes its `apply()` result to `dataset_from_iterator` or the corresponding asynchronous adapter.

Keep constructors free of mutable default arguments. Prefer `opts: dict[str, Any] | None = None` and assign `self.opts = opts or {}`.

## Design guidance

- Yield strings only; dataset conversion is handled by the registry.
- Avoid network work in `__init__`; perform it in `apply()` so failures occur during execution.
- Treat values from `opts` as untrusted configuration and validate them before use.
- Do not log credentials, authorization headers, or complete sensitive prompts.
- Make cancellation and empty results explicit for long-running asynchronous modules.
