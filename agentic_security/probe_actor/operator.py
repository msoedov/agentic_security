import asyncio
from typing import Any

from pydantic_ai import Agent, RunContext
from pydantic import  BaseModel, Field
from typing import Optional, List, Dict, Any


class AgentSpecification(BaseModel):
    name: Optional[str] = Field(None, description="Name of the LLM/agent")
    version: Optional[str] = Field(None, description="Version of the LLM/agent")
    description: Optional[str] = Field(None, description="Description of the LLM/agent")
    capabilities: Optional[List[str]] = Field(None, description="List of capabilities")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Configuration settings")

# Define the OperatorToolBox class
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
        # Validate the tool box based on the specification
        if not self.spec.name or not self.spec.version:
            self.failures.append("Invalid specification: Name or version is missing.")
            return False
        if not self.datasets:
            self.failures.append("No datasets provided.")
            return False
        return True

    def stop(self) -> None:
        # Stop the tool box
        print("Stopping the toolbox...")

    def run(self) -> None:
        # Run the tool box
        print("Running the toolbox...")

    def get_results(self) -> list[dict[str, Any]]:
        # Get the results
        return self.datasets

    def get_failures(self) -> list[str]:
        # Handle failure
        return self.failures

    def run_operation(self, operation: str) -> str:
        # Run an operation based on the specification
        if operation not in ["dataset1", "dataset2", "dataset3"]:
            self.failures.append(f"Operation '{operation}' failed: Dataset not found.")
            return f"Operation '{operation}' failed: Dataset not found."
        return f"Operation '{operation}' executed successfully."


# Initialize OperatorToolBox with AgentSpecification
spec = AgentSpecification(
    name="GPT-4",
    version="4.0",
    description="A powerful language model",
    capabilities=["text-generation", "question-answering"],
    configuration={"max_tokens": 100}
)

# dataset_manager_agent.py


# Initialize OperatorToolBox
toolbox = OperatorToolBox(
    spec=spec, datasets=["dataset1", "dataset2", "dataset3"]
)

# Define the agent with OperatorToolBox as its dependency
dataset_manager_agent = Agent(
    model="gpt-4",
    deps_type=OperatorToolBox,
    result_type=str,  # The agent will return string results
    system_prompt="You can validate the toolbox, run operations, and retrieve results or failures.",
)


@dataset_manager_agent.tool
async def validate_toolbox(ctx: RunContext[OperatorToolBox]) -> str:
    """Validate the OperatorToolBox."""
    is_valid = ctx.deps.validate()
    if is_valid:
        return "ToolBox validation successful."
    else:
        return "ToolBox validation failed."


@dataset_manager_agent.tool
async def execute_operation(ctx: RunContext[OperatorToolBox], operation: str) -> str:
    """Execute an operation on a dataset."""
    result = ctx.deps.run_operation(operation)
    return result


@dataset_manager_agent.tool
async def retrieve_results(ctx: RunContext[OperatorToolBox]) -> str:
    """Retrieve the results of operations."""
    results = ctx.deps.get_results()
    if results:
        formatted_results = "\n".join([f"{op}: {res}" for op, res in results.items()])
        return f"Operation Results:\n{formatted_results}"
    else:
        return "No operations have been executed yet."


@dataset_manager_agent.tool
async def retrieve_failures(ctx: RunContext[OperatorToolBox]) -> str:
    """Retrieve the list of failures."""
    failures = ctx.deps.get_failures()
    if failures:
        formatted_failures = "\n".join(failures)
        return f"Failures:\n{formatted_failures}"
    else:
        return "No failures recorded."


# Synchronous run example
def run_dataset_manager_agent_sync():
    prompts = [
        "Validate the toolbox.",
        "Execute operation on 'dataset2'.",
        "Execute operation on 'dataset4'.",  # This should fail
        "Retrieve the results.",
        "Retrieve any failures.",
    ]

    for prompt in prompts:
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
    ]

    for prompt in prompts:
        result = await dataset_manager_agent.run(prompt, deps=toolbox)
        print(f"Prompt: {prompt}")
        print(f"Response: {result.data}\n")


if __name__ == "__main__":
    # Run synchronous example
    run_dataset_manager_agent_sync()

    # Run asynchronous example
    asyncio.run(run_dataset_manager_agent_async())
