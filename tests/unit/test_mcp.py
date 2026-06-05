import pytest

from agentic_security.mcp.client import run


@pytest.mark.asyncio
async def test_mcp_client_lists_agentic_security_tools():
    """Test that the MCP client can discover the server tools."""
    prompts, resources, tools = await run()
    tool_names = {tool.name for tool in tools.tools}

    assert prompts is not None
    assert resources is not None
    assert {
        "verify_llm",
        "start_scan",
        "stop_scan",
        "get_data_config",
        "get_spec_templates",
    }.issubset(tool_names)
