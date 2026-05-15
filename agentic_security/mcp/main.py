import logging

import httpx
from mcp.server.fastmcp import FastMCP

# Configure module-level logger
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP(
    name="Agentic Security MCP Server",
    dependencies=["httpx"],
)

# FastAPI Server Configuration
AGENTIC_SECURITY = "http://0.0.0.0:8718"


@mcp.tool()
async def verify_llm(spec: str) -> dict:
    """
    Verify an LLM model specification using the FastAPI server

    Returns:
        dict: containing the verification result form the FastAPI server

    Args: spect(str):  The specification of the LLM model to verify.

    """
    url = f"{AGENTIC_SECURITY}/verify"
    logger.debug("Verifying LLM spec at %s", url)
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json={"spec": spec})
        logger.info("verify_llm response status: %s", response.status_code)
        return response.json()


@mcp.tool()
async def start_scan(
    llmSpec: str,
    maxBudget: int,
    optimize: bool = False,
    enableMultiStepAttack: bool = False,
) -> dict:
    """
    Start an LLM security scan via the FastAPI server.
    Returns:
        dict: The scan initiation result from the FastAPI server.

    Args:
        llmSpec (str): The specification of the LLM model.
        maxBudget (int): The maximum budget for the scan.
        optimize (bool, optional): Whether to enable optimization during scanning. Defaults to False.
        enableMultiStepAttack (bool, optional): Whether to enable multi-step attack

    """
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
    logger.debug(
        "Starting scan for spec=%r maxBudget=%d optimize=%s enableMultiStepAttack=%s",
        llmSpec,
        maxBudget,
        optimize,
        enableMultiStepAttack,
    )
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        logger.info("start_scan response status: %s", response.status_code)
        return response.json()


@mcp.tool()
async def stop_scan() -> dict:
    """Stop an ongoing scan via the FastAPI server.

    Returns:
        dict: The confirmation from the FastAPI server that the scan has been stopped.
    """
    url = f"{AGENTIC_SECURITY}/stop"
    logger.debug("Stopping scan at %s", url)
    async with httpx.AsyncClient() as client:
        response = await client.post(url)
        logger.info("stop_scan response status: %s", response.status_code)
        return response.json()


@mcp.tool()
async def get_data_config() -> list:
    """
    Retrieve data configuration from the FastAPI server.

    Returns:
        list: The response from the FastAPI server, confirming the scan has been stopped.
    """
    url = f"{AGENTIC_SECURITY}/v1/data-config"
    logger.debug("Fetching data config from %s", url)
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        logger.info("get_data_config response status: %s", response.status_code)
        return response.json()


@mcp.tool()
async def get_spec_templates() -> list:
    """
    Retrieve data configuration from the FastAPI server.

    Returns:
        list: The LLM specification templates from the FastAPI server.
    """
    url = f"{AGENTIC_SECURITY}/v1/llm-specs"
    logger.debug("Fetching spec templates from %s", url)
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        logger.info("get_spec_templates response status: %s", response.status_code)
        return response.json()


# Run the MCP server
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mcp.run()
