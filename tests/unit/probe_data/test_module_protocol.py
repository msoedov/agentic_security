import asyncio
from collections.abc import AsyncIterator, Iterator

from agentic_security.probe_data.modules import ModuleProtocol


class SyncModule:
    def __init__(self) -> None:
        self.prompt_groups = ["one"]
        self.tools_inbox: asyncio.Queue[object] = asyncio.Queue()
        self.opts: dict[str, object] = {}

    def apply(self) -> Iterator[str]:
        yield from self.prompt_groups


class AsyncModule:
    def __init__(self) -> None:
        self.prompt_groups = ["one"]
        self.tools_inbox: asyncio.Queue[object] = asyncio.Queue()
        self.opts: dict[str, object] = {}

    async def apply(self) -> AsyncIterator[str]:
        for prompt in self.prompt_groups:
            yield prompt


def test_sync_module_matches_protocol() -> None:
    assert isinstance(SyncModule(), ModuleProtocol)


def test_async_module_matches_protocol() -> None:
    assert isinstance(AsyncModule(), ModuleProtocol)
