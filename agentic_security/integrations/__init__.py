import asyncio
from typing import Protocol


class IntegrationProto(Protocol):
    def __init__(
        self, prompt_groups: list, tools_inbox: asyncio.Queue, opts: dict = {}
    ): ...

    async def apply(self) -> list: ...
