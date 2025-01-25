## Module Interface Documentation

The `Module` class interface provides a standardized way to create and use modules in the `agentic_security` project.

Here is an example of a module that implements the `ModuleProtocol` interface. This example shows how to create a module that processes prompts and sends results to a queue.


```python
from typing import List, Dict, Any, AsyncGenerator
import asyncio
from .module_protocol import ModuleProtocol

class ModuleProtocol(ModuleProtocol):
    def __init__(self, prompt_groups: List[Any], tools_inbox: asyncio.Queue, opts: Dict[str, Any]):
        self.prompt_groups = prompt_groups
        self.tools_inbox = tools_inbox
        self.opts = opts

    async def apply(self) -> AsyncGenerator[str, None]:
        for group in self.prompt_groups:
            await asyncio.sleep(1) 
            result = f"Processed {group}"
            await self.tools_inbox.put(result)
            yield result
```

#### Usage Example

```python
import asyncio
import ModuleProtocol

tools_inbox = asyncio.Queue()
prompt_groups = ["group1", "group2"]
opts = {"max_prompts": 1000, "batch_size": 100}

module = ModuleProtocol(prompt_groups, tools_inbox, opts)

async def main():
    async for result in module.apply():
        print(result)

asyncio.run(main())
```

