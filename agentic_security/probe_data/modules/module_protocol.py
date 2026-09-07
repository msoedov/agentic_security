""":mod:`module_protocol` -- Base protocol for probe data modules.

Defines the abstract Protocol that all probe data modules must implement,
providing a standardized interface for module initialization and execution.

See Also:
    :mod:`agentic_security.probe_data.modules.garak_tool`
    :mod:`agentic_security.probe_data.modules.fine_tuned`
    :mod:`agentic_security.probe_data.modules.inspect_ai_tool`
    :mod:`agentic_security.probe_data.modules.rl_model`
    :doc:`/external_module`
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ModuleProtocol(Protocol):
    """:class:`Protocol` defining the interface for probe data modules.

    All modules in :mod:`agentic_security.probe_data.modules` share the same
    constructor signature and the same async ``apply`` generator method.
    The protocol captures these shared elements to support type checking.

    Attributes:
        prompt_groups: List of prompt groups to be processed.
        tools_inbox: Async queue that receives tool execution results.
        opts: Module-specific configuration dictionary.

    Note:
        Use the concrete :class:`Module` base class rather than this
        protocol directly. This protocol exists to document the shared
        interface and to enable runtime type checking.
    """

    prompt_groups: list[Any]
    tools_inbox: asyncio.Queue
    opts: dict

    async def apply(self) -> AsyncGenerator[str]:
        """Execute the module and yield result messages.

        Yields:
            str: Result messages generated during module execution.
        """
        ...
