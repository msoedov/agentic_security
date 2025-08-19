import httpx
from mcp.server.fastmcp import FastMCP

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
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json={"spec": spec})
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as e:
        return {"error": f"Request timed out: {str(e)}"}
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}: {str(e)}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


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
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as e:
        return {"error": f"Request timed out: {str(e)}"}
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}: {str(e)}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def stop_scan() -> dict:
    """Stop an ongoing scan via the FastAPI server.

    Returns:
        dict: The confirmation from the FastAPI server that the scan has been stopped.
    """
    url = f"{AGENTIC_SECURITY}/stop"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as e:
        return {"error": f"Request timed out: {str(e)}"}
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}: {str(e)}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def get_data_config() -> list:
    """
    Retrieve data configuration from the FastAPI server.

    Returns:
        list: The response from the FastAPI server, confirming the scan has been stopped.
    """
    url = f"{AGENTIC_SECURITY}/v1/data-config"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as e:
        return {"error": f"Request timed out: {str(e)}"}
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}: {str(e)}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@mcp.tool()
async def get_spec_templates() -> list:
    """
    Retrieve data configuration from the FastAPI server.

    Returns:
        list: The LLM specification templates from the FastAPI server.
    """
    url = f"{AGENTIC_SECURITY}/v1/llm-specs"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    except httpx.TimeoutException as e:
        return {"error": f"Request timed out: {str(e)}"}
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}: {str(e)}"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


# Run the MCP server
if __name__ == "__main__":
    mcp.run()
