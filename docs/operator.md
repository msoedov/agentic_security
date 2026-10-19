# Agent operator (experimental)

The module `agentic_security.probe_actor.operator` is a prototype. An LLM agent uses tools to examine datasets and to test the built-in LLM specs.

> **CAUTION:** This module is not complete. `run_operation` accepts only the names `dataset1`, `dataset2`, and `dataset3`. The `run()` and `stop()` methods do nothing.

> **NOTE:** The module imports `pydantic_ai`. The package does not install `pydantic_ai`. Install it yourself before you import the module. The agent uses the `gpt-4` model, so you must also set `OPENAI_API_KEY`.

## Classes

`AgentSpecification` is a pydantic model with these fields: `name`, `version`, `description`, `capabilities`, `configuration`.

`OperatorToolBox(spec, datasets)` keeps the specification, the datasets, the failures, and the built-in LLM specs.

| Method | Description |
| --- | --- |
| `get_spec()` | Returns the `AgentSpecification`. |
| `get_datasets()` | Returns the datasets. |
| `validate()` | Returns `True` if the toolbox has a specification and datasets. |
| `run_operation(name)` | Returns a success message for a known dataset name. Records a failure for an unknown name. |
| `get_results()` | Returns the datasets. |
| `get_failures()` | Returns the recorded failures. |
| `test_with_prompt(index, prompt)` | Sends a prompt with the built-in LLM spec at `index`. This method is async. |

## Agent tools

The agent `dataset_manager_agent` has these tools:

| Tool | Description |
| --- | --- |
| `validate_toolbox` | Validates the toolbox. |
| `execute_operation` | Runs an operation on a dataset. |
| `retrieve_results` | Returns the results. |
| `retrieve_failures` | Returns the failures. |
| `list_llm_specs` | Lists the built-in LLM specs. |
| `test_llm_with_prompt` | Sends a prompt with one LLM spec. |

## Example

```python
from agentic_security.probe_actor.operator import (
    AgentSpecification,
    OperatorToolBox,
    dataset_manager_agent,
)

spec = AgentSpecification(
    name="GPT-4",
    version="4.0",
    description="A language model",
    capabilities=["text-generation"],
    configuration={"max_tokens": 100},
)
toolbox = OperatorToolBox(spec=spec, datasets=["dataset1", "dataset2"])

for prompt in ["Validate the toolbox.", "Execute operation on 'dataset2'.", "Retrieve any failures."]:
    result = dataset_manager_agent.run_sync(prompt, deps=toolbox)
    print(result.data)
```
