import httpx
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP(
    name="Agentic Security MCP Server",
    description="MCP server to interact with LLM scanning test",
    dependencies=["httpx"],
)

# FastAPI Server Configuration
AGENTIC_SECURITY = "http://0.0.0.0:8718"


@mcp.tool()
async def verify_llm(spec: str) -> dict:
    """Verify an LLM model specification using the FastAPI server."""
    url = f"{AGENTIC_SECURITY}/verify"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json={"spec": spec})
        return response.json()


@mcp.tool()
async def start_scan(
    llmSpec: str,
    maxBudget: int,
    optimize: bool = False,
    enableMultiStepAttack: bool = False,
) -> dict:
    """Start an LLM security scan via the FastAPI server."""
    url = f"{AGENTIC_SECURITY}/scan"
    payload = {
        "llmSpec": llmSpec,
        "maxBudget": maxBudget,
        "datasets": [],
        "optimize": optimize,
        "enableMultiStepAttack": enableMultiStepAttack,
        "probe_datasets": [],
        "secrets": {},
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        return response.json()


@mcp.tool()
async def stop_scan() -> dict:
    """Stop an ongoing scan via the FastAPI server."""
    url = f"{AGENTIC_SECURITY}/stop"
    async with httpx.AsyncClient() as client:
        response = await client.post(url)
        return response.json()


@mcp.tool()
async def get_data_config() -> list:
    """Retrieve data configuration from the FastAPI server."""
    url = f"{AGENTIC_SECURITY}/v1/data-config"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()


@mcp.tool()
async def get_spec_templates() -> list:
    """Retrieve data configuration from the FastAPI server."""
    url = f"{AGENTIC_SECURITY}/v1/llm-specs"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()


# Run the MCP server
if __name__ == "__main__":
    mcp.run()
