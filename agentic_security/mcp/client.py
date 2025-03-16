import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python",  # Executable
    args=["agentic_security/mcp/main.py"],  # Your server script
    env=None,  # Optional environment variables
)


async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # List available prompts, resources, and tools
            prompts = await session.list_prompts()
            print(f"Available prompts: {prompts}")

            resources = await session.list_resources()
            print(f"Available resources: {resources}")

            tools = await session.list_tools()
            print(f"Available tools: {tools}")

            # Call the echo tool
            echo_result = await session.call_tool(
                "echo_tool", arguments={"message": "Hello from client!"}
            )
            print(f"Tool result: {echo_result}")

            # # Read the echo resource
            # echo_content, mime_type = await session.read_resource(
            #     "echo://Hello_resource"
            # )
            # print(f"Resource content: {echo_content}")
            # print(f"Resource MIME type: {mime_type}")

            # # Get and use the echo prompt
            # prompt_result = await session.get_prompt(
            #     "echo_prompt", arguments={"message": "Hello prompt!"}
            # )
            # print(f"Prompt result: {prompt_result}")

            # You can perform additional operations here as needed


if __name__ == "__main__":
    asyncio.run(run())
