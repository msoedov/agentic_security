import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agentic_security.logutils import logger


def build_server_params() -> StdioServerParameters:
    """Create server parameters for a stdio MCP client session."""
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "agentic_security.mcp.main"],
        env=None,
    )


async def run() -> None:
    try:
        server_params = build_server_params()
        logger.info(
            "Starting stdio client session with server parameters: %s", server_params
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                logger.info("Initializing client session...")
                await session.initialize()

                logger.info("Listing available prompts...")
                prompts = await session.list_prompts()
                logger.info(f"Available prompts: {prompts}")

                logger.info("Listing available resources...")
                resources = await session.list_resources()
                logger.info(f"Available resources: {resources}")

                logger.info("Listing available tools...")
                tools = await session.list_tools()
                logger.info(f"Available tools: {tools}")
                logger.info(
                    "Available MCP tool names: %s",
                    ", ".join(tool.name for tool in tools.tools),
                )

                logger.info("Client operations completed successfully.")
                return prompts, resources, tools
    except Exception as e:
        logger.error(f"An error occurred during client operations: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(run())
