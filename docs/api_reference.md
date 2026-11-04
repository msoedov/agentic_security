# API reference

The server (`agentic_security server`) has test endpoints. Use them to test a spec before you scan a real target.

## POST /v1/self-probe

A mock LLM for text. It refuses approximately 80% of prompts at random.

Request body:

```json
{"prompt": "<<PROMPT>>"}
```

The response has the OpenAI chat-completion format.

## POST /v1/self-probe-image

A mock LLM for images. It ignores the request body and always gives the same response.

## POST /v1/self-probe-file

A mock audio transcription endpoint. It accepts a multipart upload.

| Part | Description |
| --- | --- |
| `file` | An `.m4a`, `.mp3`, or `.wav` file. |
| `model` | Optional. The default is `whisper-large-v3`. |

The request must have the header `Authorization: Bearer <any value>`. The endpoint does not examine the key. The response is `{"text": "...", "model": "..."}`.

## Other endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Returns `{"status": "ok"}`. |
| GET | `/v1/llm-specs` | Returns the built-in spec templates. |
| GET | `/v1/data-config` | Returns the dataset registry. The response is very large. |
| POST | `/verify` | Sends a test request with a spec. |
| POST | `/scan` | Starts a scan. The response is a stream of JSON lines. |
| POST | `/stop` | Stops the current scan. |
| POST | `/scan-csv` | Starts a scan with an uploaded CSV file. |
| GET | `/failures` | Returns the failures of the last scan. |
