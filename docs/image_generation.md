# Image Generation System

The image generation system creates visual probes for security testing by converting text prompts into images. This document explains its architecture and implementation.

## Overview

The system:

1. Converts text datasets into image datasets
1. Generates images using matplotlib
1. Encodes images for transmission
1. Integrates with the LLM probing system

## Core Components

### Image Generation

```python
@cache_to_disk()
def generate_image(prompt: str) -> bytes:
    """
    Generates a JPEG image containing the provided text prompt
    """
    # Create figure with light blue background
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.set_facecolor("lightblue")

    # Add centered text
    ax.text(
        0.5, 0.5,
        prompt,
        fontsize=16,
        ha="center",
        va="center",
        wrap=True,
        color="darkblue"
    )

    # Save to buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format="jpeg", bbox_inches="tight")
    return buffer.getvalue()
```

### Dataset Conversion

```python
def generate_image_dataset(text_dataset: list[ProbeDataset]) -> list[ImageProbeDataset]:
    """
    Converts text datasets into image datasets
    """
    image_datasets = []

    for dataset in text_dataset:
        image_prompts = [
            generate_image(prompt)
            for prompt in tqdm(dataset.prompts)
        ]

        image_datasets.append(ImageProbeDataset(
            test_dataset=dataset,
            image_prompts=image_prompts
        ))

    return image_datasets
```

### Image Encoding

```python
def encode(image: bytes) -> str:
    """
    Encodes image bytes into base64 data URL
    """
    encoded = base64.b64encode(image).decode("utf-8")
    return "data:image/jpeg;base64," + encoded
```

## Integration

### RequestAdapter

The RequestAdapter class integrates image generation with LLM probing:

```python
class RequestAdapter:
    def __init__(self, llm_spec):
        if not llm_spec.has_image:
            raise ValueError("LLMSpec must have an image")
        self.llm_spec = llm_spec

    async def probe(self, prompt: str, encoded_image: str = "",
                   encoded_audio: str = "", files={}) -> httpx.Response:
        encoded_image = generate_image(prompt)
        encoded_image = encode(encoded_image)
        return await self.llm_spec.probe(prompt, encoded_image, encoded_audio, files)
```

## Key Features

- **Caching**: Generated images are cached to disk using @cache_to_disk
- **Progress Tracking**: tqdm progress bars for dataset conversion
- **Error Handling**: Validates LLM specifications before probing
- **Standard Formats**: Uses JPEG format with base64 encoding

## Configuration

The system is configured through:

1. Figure size (6x4 inches)
1. Background color (light blue)
1. Text styling (16pt dark blue centered text)
1. Image format (JPEG)

## Limitations

- Currently only supports text-based image generation
- Fixed visual style and formatting
- Requires matplotlib and associated dependencies
