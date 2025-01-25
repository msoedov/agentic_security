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

## Conclusion

The `probe_data` module provides essential functionality for handling and transforming datasets within the Agentic Security project. This documentation serves as a guide to understanding and utilizing the module's capabilities.
