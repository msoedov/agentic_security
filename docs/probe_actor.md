# Probe Actor Module Documentation

The `probe_actor` module is a critical component of the Agentic Security project, responsible for generating prompts, performing scans, and handling refusal checks. This documentation provides an overview of the module's structure and functionality.

## Files and Key Components

### fuzzer.py
- **Functions:**
  - `async def generate_prompts(...)`: Asynchronously generates prompts for scanning.
  - `def multi_modality_spec(llm_spec)`: Defines specifications for multi-modality.
  - `async def process_prompt(...)`: Processes a given prompt asynchronously.
  - `async def perform_single_shot_scan(...)`: Performs a single-shot scan asynchronously.
  - `async def perform_many_shot_scan(...)`: Performs a many-shot scan asynchronously.
  - `def scan_router(...)`: Routes scan requests.

### refusal.py
- **Functions:**
  - `def check_refusal(response: str, refusal_phrases: list = REFUSAL_MARKS) -> bool`: Checks if a response contains refusal phrases.
  - `def refusal_heuristic(request_json)`: Applies heuristics to determine refusal.

## Usage Examples

### Performing a Single-Shot Scan
```python
from agentic_security.probe_actor.fuzzer import perform_single_shot_scan

await perform_single_shot_scan(prompt="Test prompt")
```

### Checking for Refusal
```python
from agentic_security.probe_actor.refusal import check_refusal

is_refusal = check_refusal(response="I'm sorry, I can't do that.")
```

## Conclusion

The `probe_actor` module provides essential functionality for generating prompts, performing scans, and handling refusal checks within the Agentic Security project. This documentation serves as a guide to understanding and utilizing the module's capabilities.
