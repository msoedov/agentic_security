import os
import asyncio
import logging
from typing import Any, List, Dict

import httpx
from pydantic import BaseModel, Field, ConfigDict
from crewai import Agent, Task, Crew
from crewai_tools import tool

# Assuming LLMSpec is defined elsewhere; placeholder import
from agentic_security.http_spec import LLMSpec

LLM_SPECS = []  # Populate with LLM spec strings if needed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define AgentSpecification model
class AgentSpecification(BaseModel):
    name: str | None = Field(None, description="Name of the LLM/agent")
    version: str | None = Field(None, description="Version of the LLM/agent")
    description: str | None = Field(None, description="Description of the LLM/agent")
    capabilities: List[str] | None = Field(None, description="List of capabilities")
    configuration: Dict[str, Any] | None = Field(
        None, description="Configuration settings"
    )
    endpoint: str | None = Field(None, description="Endpoint URL of the deployed agent")

    model_config = ConfigDict(arbitrary_types_allowed=True)


# Define OperatorToolBox class (unchanged from original)
class OperatorToolBox:
    def __init__(self, spec: AgentSpecification, datasets: List[Dict[str, Any]]):
        self.spec = spec
        self.datasets = datasets
        self.failures = []
        self.llm_specs = [LLMSpec.from_string(spec) for spec in LLM_SPECS]

    def get_spec(self) -> AgentSpecification:
        return self.spec

    def get_datasets(self) -> List[Dict[str, Any]]:
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

    async def test_llm_spec(self, llm_spec: LLMSpec, user_prompt: str) -> str:
        try:
            response = await llm_spec.verify()
            response.raise_for_status()
            logger.info(f"Verification succeeded for {llm_spec.url}")

            test_response = await llm_spec.probe(user_prompt)
            test_response.raise_for_status()
            response_data = test_response.json()
            return f"Test succeeded for {llm_spec.url}: {response_data}"
        except httpx.HTTPStatusError as e:
            self.failures.append(f"HTTP error occurred: {e}")
            logger.error(f"Test failed for {llm_spec.url}: {e}")
            return f"Test failed for {llm_spec.url}: {e}"
        except Exception as e:
            self.failures.append(f"An error occurred: {e}")
            logger.error(f"Test failed for {llm_spec.url}: {e}")
            return f"Test failed for {llm_spec.url}: {e}"

    async def test_with_prompt(self, spec_index: int, user_prompt: str) -> str:
        if not 0 <= spec_index < len(self.llm_specs):
            return f"Invalid spec index: {spec_index}. Valid range is 0 to {len(self.llm_specs) - 1}"
        llm_spec = self.llm_specs[spec_index]
        return await self.test_llm_spec(llm_spec, user_prompt)


# Define CrewAI Tools
@tool("validate_toolbox")
def validate_toolbox(toolbox: OperatorToolBox) -> str:
    """Validate the toolbox configuration."""
    is_valid = toolbox.validate()
    return (
        "ToolBox validation successful." if is_valid else "ToolBox validation failed."
    )


@tool("execute_operation")
def execute_operation(toolbox: OperatorToolBox, operation: str) -> str:
    """Execute a dataset operation."""
    return toolbox.run_operation(operation)


@tool("retrieve_results")
def retrieve_results(toolbox: OperatorToolBox) -> str:
    """Retrieve the results of operations."""
    results = toolbox.get_results()
    return (
        f"Operation Results:\n{results}"
        if results
        else "No operations have been executed yet."
    )


@tool("retrieve_failures")
def retrieve_failures(toolbox: OperatorToolBox) -> str:
    """Retrieve recorded failures."""
    failures = toolbox.get_failures()
    return f"Failures:\n{failures}" if failures else "No failures recorded."


@tool("list_llm_specs")
def list_llm_specs(toolbox: OperatorToolBox) -> str:
    """List available LLM specifications."""
    spec_list = "\n".join(
        f"{i}: {spec.url}" for i, spec in enumerate(toolbox.llm_specs)
    )
    return f"Available LLM Specs:\n{spec_list}"


@tool("test_llm_with_prompt")
async def test_llm_with_prompt(
    toolbox: OperatorToolBox, spec_index: int, user_prompt: str
) -> str:
    """Test an LLM spec with a user prompt."""
    return await toolbox.test_with_prompt(spec_index, user_prompt)


# Setup OperatorToolBox
spec = AgentSpecification(
    name="DeepSeek Chat",
    version="1.0",
    description="A powerful language model",
    capabilities=["text-generation", "question-answering"],
    configuration={"max_tokens": 100},
)
toolbox = OperatorToolBox(
    spec=spec, datasets=[{"id": "dataset1"}, {"id": "dataset2"}, {"id": "dataset3"}]
)

# Define CrewAI Agent
dataset_manager_agent = Agent(
    role="Dataset Manager",
    goal="Manage and operate the OperatorToolBox to validate configurations, run operations, and test LLMs.",
    backstory="An expert in dataset management and LLM testing, designed to assist with toolbox operations.",
    verbose=True,
    llm="openai",  # Using OpenAI-compatible API for DeepSeek; adjust if DeepSeek has a specific ID
    tools=[
        validate_toolbox,
        execute_operation,
        retrieve_results,
        retrieve_failures,
        list_llm_specs,
        test_llm_with_prompt,
    ],
    allow_delegation=False,  # Single agent, no delegation needed
)

# Define Tasks
tasks = [
    Task(
        description="Validate the toolbox configuration.",
        agent=dataset_manager_agent,
        expected_output="A string indicating whether validation succeeded or failed.",
    ),
    Task(
        description="List available LLM specifications.",
        agent=dataset_manager_agent,
        expected_output="A string listing available LLM specs.",
    ),
    Task(
        description="Guide the user to test an LLM with the prompt: 'Tell me a short story about a robot'. Suggest listing specs first.",
        agent=dataset_manager_agent,
        expected_output="A string suggesting the user list specs and proceed with testing.",
    ),
]

# Define Crew
crew = Crew(
    agents=[dataset_manager_agent],
    tasks=tasks,
    verbose=2,  # Detailed logging
)


# Async wrapper to handle async tools
async def run_crew():
    # Since CrewAI's process() is synchronous but our tool is async, we need to run it in an event loop
    result = (
        crew.kickoff()
    )  # Synchronous call; async tools are awaited internally by CrewAI
    print("\nCrew Results:")
    for task_result in result:
        print(f"Task: {task_result.description}")
        print(f"Output: {task_result.output}\n")

    # Handle user interaction for LLM testing
    print("Please select a spec index from the listed specs and confirm to proceed.")
    user_input = (
        input("Enter spec index and 'yes' to confirm (e.g., '0 yes'): ").strip().split()
    )
    if len(user_input) == 2 and user_input[1].lower() == "yes":
        try:
            spec_index = int(user_input[0])
            user_prompt = "Tell me a short story about a robot"
            # Create a new task for testing
            test_task = Task(
                description=f"Test LLM at index {spec_index} with prompt: '{user_prompt}'",
                agent=dataset_manager_agent,
                expected_output="A string with the test result from the LLM.",
            )
            test_crew = Crew(
                agents=[dataset_manager_agent], tasks=[test_task], verbose=2
            )
            test_result = test_crew.kickoff()
            print(f"Test Output: {test_result[0].output}\n")
        except ValueError:
            print("Invalid spec index provided.\n")
    else:
        print("Test canceled. Please provide a valid index and confirmation.\n")


# Ensure DeepSeek API key is set
os.environ["OPENAI_API_KEY"] = os.environ.get(
    "DEEPSEEK_API_KEY", ""
)  # CrewAI uses OPENAI_API_KEY
os.environ["OPENAI_MODEL_NAME"] = (
    "deepseek:chat"  # Specify DeepSeek model (adjust if needed)
)

if __name__ == "__main__":
    asyncio.run(run_crew())
