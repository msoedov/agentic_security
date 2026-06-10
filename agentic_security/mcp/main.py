import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP(
    name="Agentic Security MCP Server",
    dependencies=["httpx"],
)

# FastAPI Server Configuration
AGENTIC_SECURITY = os.getenv("AGENTIC_SECURITY_URL", "http://0.0.0.0:8718")


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------


@mcp.prompt()
def security_scan_prompt(llm_spec: str, max_budget: int = 1000) -> str:
    """Generate a prompt to kick off a full LLM security scan.

    Args:
        llm_spec: The LLM specification string identifying the model endpoint.
        max_budget: Maximum number of probes to run (defaults to 1000).
    """
    logger.info(f"Generating security scan prompt for spec: {llm_spec}")
    return (
        f"Please run a security scan on the following LLM specification:\n\n"
        f"  Spec: {llm_spec}\n"
        f"  Max budget: {max_budget} probes\n\n"
        f"Use the start_scan tool to initiate the scan, then monitor progress "
        f"with get_data_config, and stop it with stop_scan when complete."
    )


@mcp.prompt()
def verify_llm_prompt(llm_spec: str) -> str:
    """Generate a prompt to verify that an LLM spec is reachable and well-formed.

    Args:
        llm_spec: The LLM specification string to verify.
    """
    logger.info(f"Generating verify LLM prompt for spec: {llm_spec}")
    return (
        f"Verify the following LLM specification is valid and reachable:\n\n"
        f"  Spec: {llm_spec}\n\n"
        f"Use the verify_llm tool and report back whether the spec is accepted "
        f"by the Agentic Security server."
    )


@mcp.prompt()
def adversarial_probe_prompt(llm_spec: str) -> str:
    """Generate a prompt for an adversarial probing session with multi-step attacks.

    Args:
        llm_spec: The LLM specification string identifying the target model.
    """
    logger.info(f"Generating adversarial probe prompt for spec: {llm_spec}")
    return (
        f"Run an adversarial probing session against the LLM described by:\n\n"
        f"  Spec: {llm_spec}\n\n"
        f"Enable multi-step attacks and optimization in the start_scan call. "
        f"After the scan finishes, summarise the most critical vulnerabilities found."
    )


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def verify_llm(spec: str) -> dict:
    """
    Verify an LLM model specification using the FastAPI server

    Returns:
        dict: containing the verification result form the FastAPI server

    Args: spect(str):  The specification of the LLM model to verify.

    """
    logger.info(f"Verifying LLM spec: {spec}")
    try:
        url = f"{AGENTIC_SECURITY}/verify"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={"spec": spec})
            return response.json()
    except Exception as e:
        logger.error(f"Error verifying LLM: {e}")
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
    logger.info(f"Starting scan for spec: {llmSpec} with budget: {maxBudget}")
    try:
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
    except Exception as e:
        logger.error(f"Error starting scan: {e}")
        raise


@mcp.tool()
async def stop_scan() -> dict:
    """Stop an ongoing scan via the FastAPI server.

    Returns:
        dict: The confirmation from the FastAPI server that the scan has been stopped.
    """
    logger.info("Stopping current scan")
    try:
        url = f"{AGENTIC_SECURITY}/stop"
        async with httpx.AsyncClient() as client:
            response = await client.post(url)
            return response.json()
    except Exception as e:
        logger.error(f"Error stopping scan: {e}")
        raise


@mcp.tool()
async def get_data_config() -> list:
    """
    Retrieve data configuration from the FastAPI server.

    Returns:
        list: The response from the FastAPI server, confirming the scan has been stopped.
    """
    logger.info("Retrieving data configuration")
    try:
        url = f"{AGENTIC_SECURITY}/v1/data-config"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.json()
    except Exception as e:
        logger.error(f"Error retrieving data config: {e}")
        raise


@mcp.tool()
async def get_spec_templates() -> list:
    """
    Retrieve data configuration from the FastAPI server.

    Returns:
        list: The LLM specification templates from the FastAPI server.
    """
    logger.info("Retrieving spec templates")
    try:
        url = f"{AGENTIC_SECURITY}/v1/llm-specs"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.json()
    except Exception as e:
        logger.error(f"Error retrieving spec templates: {e}")
        raise


# Run the MCP server
if __name__ == "__main__":
    mcp.run()
