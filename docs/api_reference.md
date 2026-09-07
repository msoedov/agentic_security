# API Reference

This section provides detailed information about the Agentic Security API.

## Endpoints

### `/v1/self-probe`

- **Method**: POST
- **Description**: Used for integration testing.
- **Request Body**:
  ```json
  {
      "prompt": "<<PROMPT>>"
  }
  ```

### `/v1/self-probe-image`

- **Method**: POST
- **Description**: Probes the image modality.
- **Request Body**:
  ```json
  [
      {
          "role": "user",
          "content": [
              {
                  "type": "text",
                  "text": "What is in this image?"
              },
              {
                  "type": "image_url",
                  "image_url": {
                      "url": "data:image/jpeg;base64,<<BASE64_IMAGE>>"
                  }
              }
          ]
      }
  ]
  ```

## Authentication

`/v1/self-probe` is an unauthenticated local test endpoint. File and image
probe routes expect an `Authorization: Bearer ...` header; the mock server
checks the header shape, not a configured API key.

## Further Reading

For more details on API usage, refer to the [Configuration](configuration.md) section.
