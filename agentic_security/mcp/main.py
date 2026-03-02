import logging
import httpx
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP(
    name="Agentic Security MCP Server",
    dependencies=["httpx"],
)
logger.info("Initialized Agentic Security MCP Server")

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
    logger.info(f"Starting LLM verification for spec: {spec[:100]}...")  # Log first 100 chars for security
    url = f"{AGENTIC_SECURITY}/verify"
    
    try:
        async with httpx.AsyncClient() as client:
            logger.debug(f"Sending POST request to {url}")
            response = await client.post(url, json={"spec": spec})
            response.raise_for_status()
            result = response.json()
            logger.info(f"LLM verification completed successfully with status: {response.status_code}")
            return result
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error during LLM verification: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during LLM verification: {str(e)}")
        raise


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
    logger.info(f"Starting security scan with budget: {maxBudget}, optimize: {optimize}, multi-step: {enableMultiStepAttack}")
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
    
    try:
        async with httpx.AsyncClient() as client:
            logger.debug(f"Sending scan request to {url} with payload keys: {list(payload.keys())}")
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Security scan initiated successfully with scan ID: {result.get('scanId', 'N/A')}")
            return result
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error during scan initiation: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during scan initiation: {str(e)}")
        raise


@mcp.tool()
async def stop_scan() -> dict:
    """Stop an ongoing scan via the FastAPI server.

    Returns:
        dict: The confirmation from the FastAPI server that the scan has been stopped.
    """
    logger.info("Attempting to stop ongoing scan")
    url = f"{AGENTIC_SECURITY}/stop"
    
    try:
        async with httpx.AsyncClient() as client:
            logger.debug(f"Sending stop request to {url}")
            response = await client.post(url)
            response.raise_for_status()
            result = response.json()
            logger.info("Scan stopped successfully")
            return result
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error while stopping scan: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while stopping scan: {str(e)}")
        raise


@mcp.tool()
async def get_data_config() -> list:
    """
    Retrieve data configuration from the FastAPI server.

    Returns:
        list: The response from the FastAPI server, confirming the scan has been stopped.
    """
    logger.info("Retrieving data configuration")
    url = f"{AGENTIC_SECURITY}/v1/data-config"
    
    try:
        async with httpx.AsyncClient() as client:
            logger.debug(f"Sending GET request to {url}")
            response = await client.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Data configuration retrieved successfully, {len(result)} items found")
            return result
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error while retrieving data config: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while retrieving data config: {str(e)}")
        raise


@mcp.tool()
async def get_spec_templates() -> list:
    """
    Retrieve data configuration from the FastAPI server.

    Returns:
        list: The LLM specification templates from the FastAPI server.
    """
    logger.info("Retrieving LLM specification templates")
    url = f"{AGENTIC_SECURITY}/v1/llm-specs"
    
    try:
        async with httpx.AsyncClient() as client:
            logger.debug(f"Sending GET request to {url}")
            response = await client.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"LLM spec templates retrieved successfully, {len(result)} templates found")
            return result
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error while retrieving spec templates: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while retrieving spec templates: {str(e)}")
        raise


# Run the MCP server
if __name__ == "__main__":
    logger.info("Starting Agentic Security MCP Server")
    mcp.run()