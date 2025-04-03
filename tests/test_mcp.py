import asyncio
from unittest.mock import AsyncMock, patch

import pytest


from agentic_security.mcp.client import run, ClientSession


# Fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_session():
    with patch("mcp.client.stdio.stdio_client") as mock_client:
        mock_read = AsyncMock()
        mock_write = AsyncMock()

        # Configures mock client such that mock responses are returned
        mock_client.return_value.__aenter__.return_value = (mock_read, mock_write)

        # Creates a mock session
        mock_session = AsyncMock(spec=ClientSession)

        # Expected responses
        mock_session.initialize = AsyncMock()
        mock_session.list_prompts = AsyncMock(return_value=["test_prompt"])
        mock_session.list_resources = AsyncMock(return_value=["test_resource"])
        mock_session.list_tools = AsyncMock(return_value=["echo_tool"])
        mock_session.call_tool = AsyncMock(return_value="Hello from client!")

        with patch("mcp.ClientSession", return_value=mock_session):
            yield mock_session


# Tests


@pytest.mark.asyncio
async def test_mcp_initialization(mock_session):
    """Test initialization success and failure cases"""
    # Test initialization success case
    await run()
    mock_session.initialize.assert_called_once()

    # Resetting the mock to test for failure case
    mock_session.initialize.reset_mock()
    mock_session.initialize.side_effect = ConnectionError("Failed to connect")

    # Test connection error
    with pytest.raises(ConnectionError):
        await run()


@pytest.mark.asyncio
async def test_mcp_list_resources(mock_session):
    """Test listing available resources"""
    await run()
    mock_session.list_resources.assert_called_once()
    assert await mock_session.list_resources() == ["test_mcp_resource"]


@pytest.mark.asyncio
async def test_mcp_list_tools(mock_session):
    """Test listing available tools"""
    await run()
    mock_session.list_tools.assert_called_once()
    assert await mock_session.list_tools() == ["echo_tool"]


@pytest.mark.asyncio
async def test_mcp_echo_tool(mock_session):
    """Test the echo tool functionality"""
    await run()
    mock_session.call_tool.assert_called_once_with(
        "echo_tool", arguments={"message": "Hello from client!"}
    )
