# Probe Data Module Documentation

The `probe_data` module is a core component of the Agentic Security project, responsible for handling datasets, generating audio and image data, and applying various transformations. This documentation provides an overview of the module's structure and functionality.

## Files and Key Components

### audio_generator.py

- **Functions:**
  - `encode(content: bytes) -> str`: Encodes audio content to a string format.
  - `generate_audio_mac_wav(prompt: str) -> bytes`: Generates audio in WAV format for macOS.
  - `generate_audioform(prompt: str) -> bytes`: Generates audio from a given prompt.
- **Classes:**
  - `RequestAdapter`: Handles requests for audio generation.

### data.py

- **Functions:**
  - `load_dataset_general(...)`: Loads datasets with general specifications.
  - `count_words_in_list(str_list)`: Counts words in a list of strings.
  - `prepare_prompts(...)`: Prepares prompts for dataset processing.
- **Classes:**
  - `Stenography`: Applies transformations to prompt groups.

### image_generator.py

- **Functions:**
  - `generate_image_dataset(...)`: Generates a dataset of images.
  - `generate_image(prompt: str) -> bytes`: Generates an image from a prompt.
- **Classes:**
  - `RequestAdapter`: Handles requests for image generation.

### models.py

- **Classes:**
  - `ProbeDataset`: Represents a dataset for probing.
  - `ImageProbeDataset`: Extends `ProbeDataset` for image data.

### msj_data.py

- **Functions:**
  - `load_dataset_generic(...)`: Loads a generic dataset.
- **Classes:**
  - `ProbeDataset`: Represents a dataset for probing.

### stenography_fn.py

- **Functions:**
  - `rot13(input_text)`: Applies ROT13 transformation.
  - `base64_encode(data)`: Encodes data in base64 format.
  - `mirror_words(text)`: Mirrors words in the text.

### rl_model.py

- **Classes:**
  - `PromptSelectionInterface`: Abstract base class for prompt selection strategies.
    - Methods:
      - `select_next_prompt(current_prompt: str, passed_guard: bool) -> str`: Selects next prompt
      - `select_next_prompts(current_prompt: str, passed_guard: bool) -> list[str]`: Selects multiple prompts
      - `update_rewards(previous_prompt: str, current_prompt: str, reward: float, passed_guard: bool) -> null`: Updates rewards
  - `RandomPromptSelector`: Basic random selection with history tracking.
    - Parameters:
      - `prompts: list[str]`: List of available prompts
      - `history_size: int = 3`: Size of history to prevent cycles
  - `CloudRLPromptSelector`: Cloud-based RL implementation with fallback.
    - Parameters:
      - `prompts: list[str]`: List of available prompts
      - `api_url: str`: URL of RL service
      - `auth_token: str = AUTH_TOKEN`: Authentication token
      - `history_size: int = 300`: Size of history
      - `timeout: int = 5`: Request timeout
      - `run_id: str = ""`: Unique run identifier
  - `QLearningPromptSelector`: Local Q-learning implementation.
    - Parameters:
      - `prompts: list[str]`: List of available prompts
      - `learning_rate: float = 0.1`: Learning rate
      - `discount_factor: float = 0.9`: Discount factor
      - `initial_exploration: float = 1.0`: Initial exploration rate
      - `exploration_decay: float = 0.995`: Exploration decay rate
      - `min_exploration: float = 0.01`: Minimum exploration rate
      - `history_size: int = 300`: Size of history
- **Module**: Main class that uses CloudRLPromptSelector.
  - Parameters:
    - `prompt_groups: list[str]`: Groups of prompts
    - `tools_inbox: asyncio.Queue`: Queue for tool communication
    - `opts: dict = {}`: Configuration options

## Usage Examples

### Generating Audio

```python
from agentic_security.probe_data.audio_generator import generate_audioform

audio_bytes = generate_audioform("Hello, world!")
```

### Loading a Dataset

```python
from agentic_security.probe_data.data import load_dataset_general

dataset = load_dataset_general("example_dataset")
```

### Using RL Model

```python
from agentic_security.probe_data.modules.rl_model import QLearningPromptSelector

prompts = ["What is AI?", "Explain machine learning"]
selector = QLearningPromptSelector(prompts)
current_prompt = "What is AI?"
next_prompt = selector.select_next_prompt(current_prompt, passed_guard=true)
selector.update_rewards(current_prompt, next_prompt, reward=1.0, passed_guard=true)
```

## Conclusion

The `probe_data` module provides essential functionality for handling and transforming datasets within the Agentic Security project. This documentation serves as a guide to understanding and utilizing the module's capabilities.
