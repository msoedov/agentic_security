## Module Interface Documentation

The ``Module`` class provides a standardized way to create and use probe data
modules in the ``agentic_security`` project.

All modules in :mod:`agentic_security.probe_data.modules` share the same
constructor signature and the same ``apply`` async generator method. See the
concrete implementations for real-world usage:

* :mod:`agentic_security.probe_data.modules.garak_tool`
* :mod:`agentic_security.probe_data.modules.fine_tuned`
* :mod:`agentic_security.probe_data.modules.inspect_ai_tool`
* :mod:`agentic_security.probe_data.modules.rl_model`

### Interface Summary

Every module class accepts three constructor arguments:

``def __init__(self, prompt_groups: list[Any], tools_inbox: asyncio.Queue, opts: dict = {}): ...``

The ``apply`` method is an async generator that yields result strings:

``async def apply(self) -> AsyncGenerator[str, None]: yield "result message"``

### Usage Example

``import asyncio``
``from agentic_security.probe_data.modules.garak_tool import Module as GarakModule``
``tools_inbox = asyncio.Queue()``
``prompt_groups = ["group_a", "group_b"]``
``opts = {"port": 8718}``
``module = GarakModule(prompt_groups, tools_inbox, opts)``
``async def main(): async for result in module.apply(): print(result)``
``asyncio.run(main())``

### Defining a Custom Module

``import asyncio``
``from typing import Any``
``class MyModule:``
``    def __init__(self, prompt_groups, tools_inbox, opts={}):``
``        self.prompt_groups = prompt_groups``
``        self.tools_inbox = tools_inbox``
``        self.opts = opts``
``    async def apply(self):``
``        for group in self.prompt_groups:``
``            result = "processed {0}".format(group)``
``            await self.tools_inbox.put({"message": result})``
``            yield result``