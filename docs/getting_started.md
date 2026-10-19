# Getting started

1. Install the package. Refer to [Installation](installation.md).
2. Start the web UI:

    ```bash
    agentic_security server
    ```

    The server uses `http://127.0.0.1:8718` by default.

3. To scan without the UI, do these steps:
    1. Create `agentic_security.toml` with `agentic_security init`.
    2. Change `llmSpec` in the file to the request for your endpoint.
    3. Run `agentic_security ci`.

For more data, refer to [CLI reference](cli.md) and [Configuration](configuration.md).
