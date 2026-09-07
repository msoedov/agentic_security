# Getting Started

1. Install the package ([installation](installation.md)).
2. Start the UI:

   ```bash
   agentic_security server
   ```

   The server listens on `http://127.0.0.1:8718` by default.

3. For a headless scan, create `agentic_security.toml` with `agentic_security init`,
   edit the `llmSpec`, then run `agentic_security ci`. See the [CLI](cli.md)
   and [configuration](configuration.md) pages.
