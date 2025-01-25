# HTTP Specification Documentation

The HTTP specification in the Agentic Security project is designed to handle various types of requests, including text, image, audio, and file uploads. This documentation provides a detailed overview of the HTTP specification and its usage.

## Overview

The HTTP specification is implemented in the `LLMSpec` class, which is used to define and execute HTTP requests. The class supports different modalities, including text, image, audio, and file uploads, and provides methods to validate and execute these requests.

## Modalities

The HTTP specification supports the following modalities:

### Text

Text-based requests are the most common type of request. The `LLMSpec` class replaces the `<<PROMPT>>` placeholder in the request body with the provided prompt.

### Image

Image-based requests include an image encoded in base64 format. The `LLMSpec` class replaces the `<<BASE64_IMAGE>>` placeholder in the request body with the provided base64-encoded image.

### Audio

Audio-based requests include an audio file encoded in base64 format. The `LLMSpec` class replaces the `<<BASE64_AUDIO>>` placeholder in the request body with the provided base64-encoded audio.

### Files

File-based requests include file uploads. The `LLMSpec` class handles multipart form data and includes the provided files in the request.

## LLMSpec Class

The `LLMSpec` class is the core of the HTTP specification. It provides the following methods and properties:

### Methods

- **`from_string(http_spec: str) -> LLMSpec`**: Parses an HTTP specification string into an `LLMSpec` object.
- **`validate(prompt: str, encoded_image: str, encoded_audio: str, files: dict) -> None`**: Validates the request parameters based on the specified modality.
- **`probe(prompt: str, encoded_image: str = "", encoded_audio: str = "", files: dict = {}) -> httpx.Response`**: Sends an HTTP request using the specified parameters.
- **`verify() -> httpx.Response`**: Verifies the HTTP specification by sending a test request.

### Properties

- **`modality: Modality`**: Returns the modality of the request (text, image, audio, or files).

## Examples

### Text Request

```python
http_spec = """
POST https://api.example.com/v1/chat/completions
Authorization: Bearer sk-xxxxxxxxx
Content-Type: application/json

{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "<<PROMPT>>"}],
    "temperature": 0.7
}
"""

spec = LLMSpec.from_string(http_spec)
response = await spec.probe("What is the capital of France?")
```

### Image Request

```python
http_spec = """
POST https://api.example.com/v1/chat/completions
Authorization: Bearer sk-xxxxxxxxx
Content-Type: application/json

{
    "model": "gpt-4-vision-preview",
    "messages": [{"role": "user", "content": "What is in this image? <<BASE64_IMAGE>>"}],
    "temperature": 0.7
}
"""

spec = LLMSpec.from_string(http_spec)
encoded_image = encode_image_base64_by_url("https://example.com/image.jpg")
response = await spec.probe("What is in this image?", encoded_image=encoded_image)
```

### Audio Request

```python
http_spec = """
POST https://api.example.com/v1/chat/completions
Authorization: Bearer sk-xxxxxxxxx
Content-Type: application/json

{
    "model": "whisper-large-v3",
    "messages": [{"role": "user", "content": "Transcribe this audio: <<BASE64_AUDIO>>"}],
    "temperature": 0.7
}
"""

spec = LLMSpec.from_string(http_spec)
encoded_audio = encode_audio_base64_by_url("https://example.com/audio.mp3")
response = await spec.probe("Transcribe this audio:", encoded_audio=encoded_audio)
```

### File Request

```python
http_spec = """
POST https://api.example.com/v1/chat/completions
Authorization: Bearer sk-xxxxxxxxx
Content-Type: multipart/form-data

{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Process this file: <<FILE>>"}],
    "temperature": 0.7
}
"""

spec = LLMSpec.from_string(http_spec)
files = {"file": ("document.txt", open("document.txt", "rb"))}
response = await spec.probe("Process this file:", files=files)
```

## Conclusion

The HTTP specification in the Agentic Security project provides a flexible and powerful way to handle various types of requests. This documentation serves as a guide to understanding and utilizing the HTTP specification effectively.
