# HTTP spec

An HTTP spec is a plain-text HTTP request. It tells the scanner how to send a prompt to the target. The `LLMSpec` class in `agentic_security.http_spec` parses and sends the request.

## Format

```http
POST https://api.openai.com/v1/chat/completions
Authorization: Bearer sk-xxxxxxxxx
Content-Type: application/json

{
  "model": "gpt-4o-mini",
  "messages": [{"role": "user", "content": "<<PROMPT>>"}]
}
```

- Line 1 is the method and the URL. The URL must start with `http://` or `https://`.
- The next lines are headers, one `Name: value` on each line.
- An empty line comes after the headers.
- The remaining lines are the body.

## Placeholders

| Placeholder | Replaced with | Modality |
| --- | --- | --- |
| `<<PROMPT>>` | The attack prompt, escaped for JSON. | Text |
| `<<BASE64_IMAGE>>` | A data URL: `data:image/jpeg;base64,...` | Image |
| `<<BASE64_AUDIO>>` | A data URL: `data:audio/mpeg;base64,...` | Audio |

The scanner sets the modality from the placeholders in the body:

- `<<BASE64_IMAGE>>` in the body sets the image modality. The scanner makes an image of each prompt.
- `<<BASE64_AUDIO>>` in the body sets the audio modality.
- `Content-Type: multipart/form-data` sets the file modality.

> **CAUTION:** The image and audio values already start with `data:...;base64,`. Do not write this prefix in the spec. Use `"url": "<<BASE64_IMAGE>>"`.

## Secrets

In a web server scan, the tool replaces `$NAME` in the body with a secret value. The value comes from `NAME` in the `[secrets]` section. Refer to [Configuration](configuration.md). The tool does not replace names in the URL or in the headers.

## File uploads

When the spec has `Content-Type: multipart/form-data`, `probe()` sends only the `files` argument. It does not send the body.

## LLMSpec methods

| Method | Description |
| --- | --- |
| `LLMSpec.from_string(text)` | Parses the spec. If the spec is not valid, it raises `InvalidHTTPSpecError`. |
| `probe(prompt, encoded_image="", encoded_audio="", files=None)` | Sends one request. Returns an `httpx.Response`. This method is async. |
| `verify()` | Sends a test request for the modality of the spec. This method is async. |
| `validate(prompt, encoded_image, encoded_audio, files)` | Raises `ValueError` if a value that the modality needs is missing. |
| `modality` | `Modality.TEXT`, `Modality.IMAGE`, or `Modality.AUDIO`. |

## Examples

### Text

```python
from agentic_security.http_spec import LLMSpec

spec = LLMSpec.from_string(open("target.http").read())
response = await spec.probe("What is the capital of France?")
```

### Image

```python
from agentic_security.http_spec import LLMSpec, encode_image_base64_by_url

spec = LLMSpec.from_string("""POST https://api.example.com/v1/chat/completions
Authorization: Bearer sk-xxxxxxxxx
Content-Type: application/json

{"messages": [{"role": "user", "content": [
  {"type": "text", "text": "<<PROMPT>>"},
  {"type": "image_url", "image_url": {"url": "<<BASE64_IMAGE>>"}}
]}]}
""")
image = encode_image_base64_by_url("https://example.com/image.jpg")
response = await spec.probe("What is in this image?", encoded_image=image)
```

### Audio

```python
from agentic_security.http_spec import encode_audio_base64_by_url

audio = encode_audio_base64_by_url("https://example.com/audio.mp3")
response = await spec.probe("Transcribe this audio.", encoded_audio=audio)
```

### File

```python
spec = LLMSpec.from_string("""POST http://127.0.0.1:8718/v1/self-probe-file
Authorization: Bearer XXXXX
Content-Type: multipart/form-data
""")
with open("sample.m4a", "rb") as f:
    response = await spec.probe("", files={"file": ("sample.m4a", f)})
```
