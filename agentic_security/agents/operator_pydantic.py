import asyncio
import logging
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import Agent, RunContext, Tool

# Assuming LLMSpec is defined elsewhere; placeholder import
from agentic_security.http_spec import LLMSpec

LLM_SPECS = []  # Populate this list with LLM spec strings if needed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define AgentSpecification model
class AgentSpecification(BaseModel):
    name: str | None = Field(None, description="Name of the LLM/agent")
    version: str | None = Field(None, description="Version of the LLM/agent")
    description: str | None = Field(None, description="Description of the LLM/agent")
    capabilities: list[str] | None = Field(None, description="List of capabilities")
    configuration: dict[str, Any] | None = Field(
        None, description="Configuration settings"
    )
    endpoint: str | None = Field(None, description="Endpoint URL of the deployed agent")

    model_config = ConfigDict(arbitrary_types_allowed=True)


# Define OperatorToolBox class
class OperatorToolBox:
    def __init__(self, spec: AgentSpecification, datasets: list[dict[str, Any]]):
        self.spec = spec
        self.datasets = datasets
        self.failures = []
        self.llm_specs = [LLMSpec.from_string(spec) for spec in LLM_SPECS]

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

    def get_results(self) -> list[dict[str, Any]]:
        return self.datasets

    def get_failures(self) -> list[str]:
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


# Define the Agent
class DatasetManagerAgent(Agent):
    model: str = "deepseek:chat"
    system_prompt: str = (
        "You are an AI agent managing an OperatorToolBox. You can validate the toolbox, run operations, "
        "retrieve results or failures, list LLM specs, and test LLM specs with user prompts. "
        "Use the provided tools to assist the user based on their request."
    )

    def __init__(self, toolbox: OperatorToolBox, **kwargs):
        super().__init__(**kwargs)
        self.toolbox = toolbox

        # Define async tools within __init__
        async def validate_toolbox(ctx: RunContext[Any]) -> str:
            is_valid = self.toolbox.validate()
            return (
                "ToolBox validation successful."
                if is_valid
                else "ToolBox validation failed."
            )

        async def execute_operation(ctx: RunContext[Any], operation: str) -> str:
            return self.toolbox.run_operation(operation)

        async def retrieve_results(ctx: RunContext[Any]) -> str:
            results = self.toolbox.get_results()
            return (
                f"Operation Results:\n{results}"
                if results
                else "No operations have been executed yet."
            )

        async def retrieve_failures(ctx: RunContext[Any]) -> str:
            failures = self.toolbox.get_failures()
            return f"Failures:\n{failures}" if failures else "No failures recorded."

        async def list_llm_specs(ctx: RunContext[Any]) -> str:
            spec_list = "\n".join(
                f"{i}: {spec.url}" for i, spec in enumerate(self.toolbox.llm_specs)
            )
            return f"Available LLM Specs:\n{spec_list}"

        async def test_llm_with_prompt(
            ctx: RunContext[Any], spec_index: int, user_prompt: str
        ) -> str:
            return await self.toolbox.test_with_prompt(spec_index, user_prompt)

        # Register tools
        self.tools = [
            Tool(
                name="validate_toolbox",
                description="Validate the toolbox configuration.",
                function=validate_toolbox,
            ),
            Tool(
                name="execute_operation",
                description="Execute a dataset operation.",
                function=execute_operation,
            ),
            Tool(
                name="retrieve_results",
                description="Retrieve the results of operations.",
                function=retrieve_results,
            ),
            Tool(
                name="retrieve_failures",
                description="Retrieve recorded failures.",
                function=retrieve_failures,
            ),
            Tool(
                name="list_llm_specs",
                description="List available LLM specifications.",
                function=list_llm_specs,
            ),
            Tool(
                name="test_llm_with_prompt",
                description="Test an LLM spec with a user prompt.",
                function=test_llm_with_prompt,
            ),
        ]


# Setup and run example
async def run_dataset_manager_agent_async():
    # Initialize OperatorToolBox with AgentSpecification
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

    # Create the agent
    agent = DatasetManagerAgent(toolbox=toolbox)

    # Example prompts
    prompts = [
        "Validate the toolbox.",
        "List available LLM specs.",
        "I want to test an LLM with my prompt: 'Tell me a short story about a robot'. Which spec index should I use?",
    ]

    for prompt in prompts:
        result = await agent.run(prompt)
        print(f"Prompt: {prompt}")
        print(f"Response: {result}\n")

        # Handle testing request
        if "test an LLM with my prompt" in prompt:
            print(
                "Please select a spec index from the list above and confirm to proceed."
            )
            # Simulate user input (replace with real input in practice)
            user_input = (
                input("Enter spec index and 'yes' to confirm (e.g., '0 yes'): ")
                .strip()
                .split()
            )
            if len(user_input) == 2 and user_input[1].lower() == "yes":
                try:
                    spec_index = int(user_input[0])
                    user_prompt = prompt.split("my prompt: ")[1].strip("'")
                    test_result = await agent.run(
                        f"Test LLM at index {spec_index} with prompt: {user_prompt}"
                    )
                    print(f"Test Response: {test_result}\n")
                except ValueError:
                    print("Invalid spec index provided.\n")
            else:
                print("Test canceled. Please provide a valid index and confirmation.\n")


if __name__ == "__main__":
    asyncio.run(run_dataset_manager_agent_async())
