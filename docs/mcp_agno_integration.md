# MCP + Agno Integration

This guide shows how to use Agentic Security's MCP server with [Agno](https://docs.agno.com/tools/mcp) agents.

## Setup

Install Agentic Security with optional Agno support:

```bash
pip install agno
```

## Starting the MCP Server

Start the Agentic Security MCP server:

```bash
python -m agentic_security.mcp.main
```

For production, use the stdio transport (default with FastMCP):

```bash
python agentic_security/mcp/main.py
```

## Examples

### Basic Verification with Agno

```python
import asyncio

from agno.agent import Agent
from agno.tools.mcp import MCPTools

from agentic_security.mcp.main import mcp


async def verify_llm_spec():
    # Connect to Agentic Security's MCP server via stdio
    mcp_tools = MCPTools(
        command="python",
        args=["agentic_security/mcp/main.py"],
    )
    await mcp_tools.connect()

    try:
        agent = Agent(
            tools=[mcp_tools],
            instructions=[
                "You are a security testing assistant.",
                "Use verify_llm to test LLM specifications for vulnerabilities.",
                "Present results clearly with risk levels.",
            ],
            markdown=True,
        )

        await agent.aprint_response(
            "Verify this LLM spec: openai/gpt-4",
            stream=True,
        )
    finally:
        await mcp_tools.close()


asyncio.run(verify_llm_spec())
```

### Running a Security Scan

```python
import asyncio

from agno.agent import Agent
from agno.tools.mcp import MCPTools


async def run_security_scan():
    mcp_tools = MCPTools(
        command="python",
        args=["agentic_security/mcp/main.py"],
    )
    await mcp_tools.connect()

    try:
        agent = Agent(
            tools=[mcp_tools],
            instructions=[
                "You are an LLM security scanning assistant.",
                "Use start_scan to initiate security scans on LLM endpoints.",
                "Use get_data_config to check available scan configurations.",
                "Report findings with severity levels.",
            ],
            markdown=True,
        )

        await agent.aprint_response(
            "Run a security scan on openai/gpt-4 with max budget 100",
            stream=True,
        )
    finally:
        await mcp_tools.close()


asyncio.run(run_security_scan())
```

### Streamable HTTP Transport

```python
import asyncio

from agno.agent import Agent
from agno.tools.mcp import MCPTools


async def run_http_transport():
    mcp_tools = MCPTools(
        transport="streamable-http",
        url="http://0.0.0.0:8718/mcp",
    )
    await mcp_tools.connect()

    try:
        agent = Agent(
            tools=[mcp_tools],
            markdown=True,
        )

        await agent.aprint_response(
            "List available security scan templates",
            stream=True,
        )
    finally:
        await mcp_tools.close()


asyncio.run(run_http_transport())
```

## Available Tools

| Tool | Description |
|---|---|
| `verify_llm` | Verify an LLM model specification |
| `start_scan` | Start an LLM security scan |
| `stop_scan` | Stop an ongoing scan |
| `get_data_config` | Retrieve data configuration |
| `get_spec_templates` | Retrieve LLM specification templates |

## Notes

- The stdio transport is recommended for local development
- For production deployments, use the streamable-http transport
- Always call `mcp_tools.close()` to clean up connections
