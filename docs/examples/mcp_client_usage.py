"""
MCP Client Usage Example for agentic_security.

This script demonstrates how to initialize the MCPClient and list available tools.
"""
import asyncio
from agentic_security.mcp.client import MCPClient

async def main():
    # 1. Initialize the client (ensure you have an MCP server running)
    # Replace the URL with your actual MCP server endpoint
    client = MCPClient(server_url="http://localhost:8080")
    
    try:
        # 2. Connect to the MCP server
        print("Connecting to MCP server...")
        await client.connect()
        
        # 3. List available tools
        tools = await client.list_tools()
        print(f"Available tools: {tools}")
        
        # 4. Example call (replace with your tool name and arguments)
        # result = await client.call_tool("tool_name", {"arg": "value"})
        # print(f"Tool result: {result}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
