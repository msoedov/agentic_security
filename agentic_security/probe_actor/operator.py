import asyncio
from typing import Any, Optional, Dict, List
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
import httpx
from httpx import LLMSpec
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentSpecification(BaseModel):
    name: Optional[str] = Field(None, description="Name of the LLM/agent")
    version: Optional[str] = Field(None, description="Version of the LLM/agent")
    description: Optional[str] = Field(None, description="Description of the LLM/agent")
    capabilities: Optional[List[str]] = Field(None, description="List of capabilities")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Configuration settings")
    endpoint: Optional[str] = Field(None, description="Endpoint URL of the deployed agent")

class OperatorToolBox:
    def __init__(self, spec: AgentSpecification, datasets: list[dict[str, Any]]):
        self.spec = spec
        self.datasets = datasets
        self.failures = []

    def get_spec(self) -> AgentSpecification:
        return self.spec

    def get_datasets(self) -> list[dict[str, Any]]:
        return self.datasets

    def validate(self) -> bool:
        if not self.spec.name or not self.spec.version:
            self.failures.append("Invalid specification: Name or version is missing.")
            return False
        if not self.datasets:
            self.failures.append("No datasets provided.")
            return False
        return True

    def stop(self) -> None:
        logger.info("Stopping the toolbox...")

    def run(self) -> None:
        logger.info("Running the toolbox...")

    def get_results(self) -> List[Dict[str, Any]]:
        return self.datasets

    def get_failures(self) -> List[str]:
        return self.failures

    def run_operation(self, operation: str) -> str:
        if operation not in ["dataset1", "dataset2", "dataset3"]:
            self.failures.append(f"Operation '{operation}' failed: Dataset not found.")
            return f"Operation '{operation}' failed: Dataset not found."
        return f"Operation '{operation}' executed successfully."

    async def test(self, description: str, sample_test: Dict[str, Any]) -> str:
        agent = Agent(
            'openai:gpt-4o',
            result_type=LLMSpec,
            system_prompt='Extract the LLM specification from the input',
        )

        async with agent.run_stream(description) as result:
            async for spec in result.stream():
                self.spec.endpoint = spec.url

                # Verify access to the endpoint
                async with httpx.AsyncClient() as client:
                    try:
                        access_response = await client.get(spec.url)
                        access_response.raise_for_status()
                    except httpx.HTTPStatusError as e:
                        self.failures.append(f"HTTP error occurred: {e}")
                        logger.error(f"Access verification failed: {e}")
                        return f"Access verification failed: {e}"
                    except Exception as e:
                        self.failures.append(f"An error occurred: {e}")
                        logger.error(f"Access verification failed: {e}")
                        return f"Access verification failed: {e}"

                # Run the sample test
                try:
                    test_response = await client.post(f"{spec.url}/test", json=sample_test)
                    test_response.raise_for_status()
                    response_data = test_response.json()
                    if "choices" in response_data and len(response_data["choices"]) > 0:
                        return f"Testing agent at {spec.url} succeeded: {response_data}"
                    else:
                        self.failures.append("Invalid response format")
                        logger.error("Sample test failed: Invalid response format")
                        return "Sample test failed: Invalid response format"
                except httpx.HTTPStatusError as e:
                    self.failures.append(f"HTTP error occurred: {e}")
                    logger.error(f"Sample test failed: {e}")
                    return f"Sample test failed: {e}"
                except Exception as e:
                    self.failures.append(f"An error occurred: {e}")
                    logger.error(f"Sample test failed: {e}")
                    return f"Sample test failed: {e}"

# Initialize OperatorToolBox with AgentSpecification
spec = AgentSpecification(
    name="GPT-4",
    version="4.0",
    description="A powerful language model",
    capabilities=["text-generation", "question-answering"],
    configuration={"max_tokens": 100},
)

toolbox = OperatorToolBox(spec=spec, datasets=["dataset1", "dataset2", "dataset3"])

# Define the agent with OperatorToolBox as its dependency
dataset_manager_agent = Agent(
    model="gpt-4",
    deps_type=OperatorToolBox,
    result_type=str,
    system_prompt="You can validate the toolbox, run operations, and retrieve results or failures.",
)

@dataset_manager_agent.tool
async def validate_toolbox(ctx: RunContext[OperatorToolBox]) -> str:
    is_valid = ctx.deps.validate()
    if is_valid:
        return "ToolBox validation successful."
    else:
        return "ToolBox validation failed."

@dataset_manager_agent.tool
async def execute_operation(ctx: RunContext[OperatorToolBox], operation: str) -> str:
    result = ctx.deps.run_operation(operation)
    return result

@dataset_manager_agent.tool
async def retrieve_results(ctx: RunContext[OperatorToolBox]) -> str:
    results = ctx.deps.get_results()
    if results:
        formatted_results = "\n".join([f"{op}: {res}" for op, res in results.items()])
        return f"Operation Results:\n{formatted_results}"
    else:
        return "No operations have been executed yet."

@dataset_manager_agent.tool
async def retrieve_failures(ctx: RunContext[OperatorToolBox]) -> str:
    failures = ctx.deps.get_failures()
    if failures:
        formatted_failures = "\n".join(failures)
        return f"Failures:\n{formatted_failures}"
    else:
        return "No failures recorded."

@dataset_manager_agent.tool
async def test_agent(ctx: RunContext[OperatorToolBox], description: str, sample_test: Dict[str, Any]) -> str:
    result = await ctx.deps.test(description, sample_test)
    return result

# Synchronous run example
def run_dataset_manager_agent_sync():
    prompts = [
        "Validate the toolbox.",
        "Execute operation on 'dataset2'.",
        "Execute operation on 'dataset4'.",  # This should fail
        "Retrieve the results.",
        "Retrieve any failures.",
        "Test my openAI compatible agent deployed at localhost:3000"
    ]

    sample_test = {
        "prompt": "Hello, how are you?",
        "max_tokens": 5
    }

    for prompt in prompts:
        if "Test my" in prompt:
            result = dataset_manager_agent.run_sync(prompt, deps=toolbox, sample_test=sample_test)
        else:
            result = dataset_manager_agent.run_sync(prompt, deps=toolbox)
        print(f"Prompt: {prompt}")
        print(f"Response: {result.data}\n")

# Asynchronous run example
async def run_dataset_manager_agent_async():
    prompts = [
        "Validate the toolbox.",
        "Execute operation on 'dataset2'.",
        "Execute operation on 'dataset4'.",  # This should fail
        "Retrieve the results.",
        "Retrieve any failures.",
        "Test my openAI compatible agent deployed at localhost:3000"
    ]

    sample_test = {
        "prompt": "Hello, how are you?",
        "max_tokens": 5
    }

    for prompt in prompts:
        if "Test my" in prompt:
            result = await dataset_manager_agent.run(prompt, deps=toolbox, sample_test=sample_test)
        else:
            result = await dataset_manager_agent.run(prompt, deps=toolbox)
        print(f"Prompt: {prompt}")
        print(f"Response: {result.data}\n")

if __name__ == "__main__":
    # Run synchronous example
    run_dataset_manager_agent_sync()

    # Run asynchronous example
    asyncio.run(run_dataset_manager_agent_async())