#!/usr/bin/env python3
"""Example MCP client for the Agentic Security stdio server.

The default command lists the tools exposed by ``agentic_security.mcp.main``.
If the Agentic Security HTTP app is running, pass ``--call`` to invoke one of
the no-argument HTTP-backed tools through MCP.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


NO_ARGUMENT_TOOLS = {"get_data_config", "get_spec_templates", "stop_scan"}


def _build_server_params(agentic_security_url: str | None) -> StdioServerParameters:
    env = os.environ.copy()
    if agentic_security_url:
        env["AGENTIC_SECURITY_URL"] = agentic_security_url

    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "agentic_security.mcp.main"],
        env=env,
    )


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


async def run_client(agentic_security_url: str | None, call_tool: str | None) -> None:
    server_params = _build_server_params(agentic_security_url)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            tool_names = [tool.name for tool in tools.tools]

            print("Available Agentic Security MCP tools:")
            for tool in tools.tools:
                description_lines = (tool.description or "").strip().splitlines()
                description = description_lines[0] if description_lines else "No description"
                print(f"- {tool.name}: {description}")

            if not call_tool:
                return

            if call_tool not in tool_names:
                raise ValueError(
                    f"Unknown tool {call_tool!r}. Available tools: {', '.join(tool_names)}"
                )
            if call_tool not in NO_ARGUMENT_TOOLS:
                raise ValueError(
                    f"{call_tool!r} requires arguments. This example only calls "
                    f"no-argument tools: {', '.join(sorted(NO_ARGUMENT_TOOLS))}"
                )

            result = await session.call_tool(call_tool, arguments={})
            print()
            print(f"{call_tool} result:")
            print(json.dumps(_jsonable(result), indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List Agentic Security MCP tools and optionally call one.",
    )
    parser.add_argument(
        "--agentic-security-url",
        default=None,
        help=(
            "Agentic Security HTTP app URL. Defaults to AGENTIC_SECURITY_URL "
            "or http://0.0.0.0:8718 in the server."
        ),
    )
    parser.add_argument(
        "--call",
        choices=sorted(NO_ARGUMENT_TOOLS),
        help="Optional no-argument MCP tool to call after listing tools.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_client(args.agentic_security_url, args.call))
