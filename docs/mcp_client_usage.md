# MCP client usage

Agentic Security exposes an MCP stdio server in `agentic_security.mcp.main`.
The example client in `examples/mcp_client_usage.py` shows how to connect to
that server, list available tools, and optionally call simple no-argument tools.

## List MCP tools

From the repository root:

```shell
python examples/mcp_client_usage.py
```

This starts the MCP server as a subprocess with:

```shell
python -m agentic_security.mcp.main
```

The client initializes an MCP session and prints the available Agentic Security
tools, including `verify_llm`, `start_scan`, `stop_scan`, `get_data_config`, and
`get_spec_templates`.

## Call an HTTP-backed tool

Some MCP tools call the Agentic Security HTTP app. Start the app in another
terminal first:

```shell
agentic_security --host 127.0.0.1 --port 8718
```

Then point the MCP server at that app and call a no-argument tool:

```shell
python examples/mcp_client_usage.py \
  --agentic-security-url http://127.0.0.1:8718 \
  --call get_spec_templates
```

You can also set `AGENTIC_SECURITY_URL` directly:

```shell
AGENTIC_SECURITY_URL=http://127.0.0.1:8718 python examples/mcp_client_usage.py --call get_data_config
```

## Use the package helper

For tests or quick local checks, `agentic_security.mcp.client.run()` creates the
same stdio session and returns the prompt, resource, and tool list results:

```python
import asyncio

from agentic_security.mcp.client import run


async def main() -> None:
    _prompts, _resources, tools = await run()
    print([tool.name for tool in tools.tools])


asyncio.run(main())
```
