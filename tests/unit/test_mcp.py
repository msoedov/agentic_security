import pytest

from agentic_security.mcp.client import run


@pytest.mark.asyncio
async def test_mcp_echo_tool():
    """Test the echo tool functionality"""
    prompts, resources, tools = await run()
    assert prompts
    assert resources
    assert tools
