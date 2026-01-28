from __future__ import annotations
import logging
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class FuzzRunnable(Protocol):
    """Protocol for objects that can be run in a fuzzing chain."""

    async def run(self, **kwargs: Any) -> str:
        ...


class FuzzNode:
    """A single node in a fuzzing chain that executes an LLM call with template variables."""

    def __init__(self, llm: Any, prompt: str) -> None:
        self._llm = llm
        self._prompt = prompt

    async def run(self, **kwargs: Any) -> str:
        full_prompt = self._render_prompt(kwargs)
        response = await self._llm.generate(full_prompt)
        return response if response else ""

    def _render_prompt(self, kwargs: dict[str, Any]) -> str:
        if not kwargs:
            return self._prompt
        result = self._prompt
        for key, value in kwargs.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    def __or__(self, other: Any) -> FuzzChain:
        if isinstance(other, FuzzChain):
            return FuzzChain([self, *other._nodes])
        if isinstance(other, FuzzNode):
            return FuzzChain([self, other])
        # Assume LLMProvider-like object
        return FuzzChain([self, FuzzNode(other, "{input}")])

    def __repr__(self) -> str:
        return f"FuzzNode(prompt={self._prompt!r})"


class FuzzChain:
    """A chain of FuzzNodes that execute sequentially, passing output as input."""

    def __init__(self, nodes: list[FuzzNode] | None = None) -> None:
        self._nodes: list[FuzzNode] = []
        if nodes:
            self._nodes.extend(nodes)

    async def run(self, **kwargs: Any) -> str:
        if not self._nodes:
            return ""
        result = ""
        for i, node in enumerate(self._nodes):
            logger.debug(f"Running node {i}: {node} with kwargs {kwargs}")
            result = await node.run(**kwargs)
            logger.debug(f"Node {i} result: {result[:100]}...")
            kwargs = {"input": result}
        return result

    def __or__(self, other: Any) -> FuzzChain:
        if isinstance(other, FuzzChain):
            return FuzzChain([*self._nodes, *other._nodes])
        if isinstance(other, FuzzNode):
            return FuzzChain([*self._nodes, other])
        # Assume LLMProvider-like object
        return FuzzChain([*self._nodes, FuzzNode(other, "{input}")])

    def __len__(self) -> int:
        return len(self._nodes)

    def __repr__(self) -> str:
        return f"FuzzChain({self._nodes!r})"
