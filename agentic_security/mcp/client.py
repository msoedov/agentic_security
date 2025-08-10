import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agentic_security.logutils import logger

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python",  # Executable
    args=["agentic_security/mcp/main.py"],  # Your server script
    env=None,  # Optional environment variables
)


async def run() -> None:
    try:
        logger.info(
            "Starting stdio client session with server parameters: %s", server_params
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection --> connection does not work
                logger.info("Initializing client session...")
                await session.initialize()

                # List available prompts, resources, and tools --> no avalialbe tools
                logger.info("Listing available prompts...")
                prompts = await session.list_prompts()
                logger.info(f"Available prompts: {prompts}")

                logger.info("Listing available resources...")
                resources = await session.list_resources()
                logger.info(f"Available resources: {resources}")

                logger.info("Listing available tools...")
                tools = await session.list_tools()
                logger.info(f"Available tools: {tools}")

                # Call the echo tool --> echo tool issue
                logger.info("Calling echo_tool with message...")
                echo_result = await session.call_tool(
                    "echo_tool", arguments={"message": "Hello from client!"}
                )
                logger.info(f"Tool result: {echo_result}")

                # # Read the echo resource
                # echo_content, mime_type = await session.read_resource(
                #     "echo://Hello_resource"
                # )
                # logger.info(f"Resource content: {echo_content}")
                # logger.info(f"Resource MIME type: {mime_type}")

                # # Get and use the echo prompt
                # prompt_result = await session.get_prompt(
                #     "echo_prompt", arguments={"message": "Hello prompt!"}
                # )
                # logger.info(f"Prompt result: {prompt_result}")

                logger.info("Client operations completed successfully.")
                return prompts, resources, tools
    except Exception as e:
        logger.error(f"An error occurred during client operations: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(run())
