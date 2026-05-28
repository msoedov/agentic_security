from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from agentic_security.logutils import logger

# Initialize MCP server
mcp = FastMCP(
    name="Agentic Security MCP Server",
    dependencies=["httpx"],
)

# FastAPI Server Configuration
AGENTIC_SECURITY = "http://0.0.0.0:8718"


def _api_error(error_type: str, message: str, **details: Any) -> dict[str, Any]:
    error = {"type": error_type, "message": message}
    error.update(details)
    return {"error": error}


def _response_body(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text


async def _request_api(
    method: str,
    path: str,
    *,
    json: dict[str, Any] | None = None,
) -> dict[str, Any] | list[Any]:
    url = f"{AGENTIC_SECURITY}{path}"
    try:
        async with httpx.AsyncClient() as client:
            request_kwargs = {}
            if json is not None:
                request_kwargs["json"] = json
            response = await client.request(method, url, **request_kwargs)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        response = exc.response
        logger.error("MCP backend returned an error: %s", exc)
        return _api_error(
            "http_status",
            str(exc),
            status_code=response.status_code,
            response=_response_body(response),
        )
    except httpx.RequestError as exc:
        logger.error("MCP backend request failed: %s", exc)
        return _api_error("request", str(exc))
    except ValueError as exc:
        logger.error("MCP backend returned invalid JSON: %s", exc)
        return _api_error("invalid_json", str(exc))


@mcp.tool()
async def verify_llm(spec: str) -> dict:
    """
    Verify an LLM model specification using the FastAPI server

    Returns:
        dict: containing the verification result form the FastAPI server

    Args: spect(str):  The specification of the LLM model to verify.

    """
    return await _request_api("POST", "/verify", json={"spec": spec})


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
    payload = {
        "llmSpec": llmSpec,
        "maxBudget": maxBudget,
        "datasets": [],
        "optimize": optimize,
        "enableMultiStepAttack": enableMultiStepAttack,
        "probe_datasets": [],
        "secrets": {},
    }
    return await _request_api("POST", "/scan", json=payload)


@mcp.tool()
async def stop_scan() -> dict:
    """Stop an ongoing scan via the FastAPI server.

    Returns:
        dict: The confirmation from the FastAPI server that the scan has been stopped.
    """
    return await _request_api("POST", "/stop")


@mcp.tool()
async def get_data_config() -> list:
    """
    Retrieve data configuration from the FastAPI server.

    Returns:
        list: The response from the FastAPI server, confirming the scan has been stopped.
    """
    return await _request_api("GET", "/v1/data-config")


@mcp.tool()
async def get_spec_templates() -> list:
    """
    Retrieve data configuration from the FastAPI server.

    Returns:
        list: The LLM specification templates from the FastAPI server.
    """
    return await _request_api("GET", "/v1/llm-specs")


# Run the MCP server
if __name__ == "__main__":
    mcp.run()
