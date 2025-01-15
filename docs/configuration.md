# Configuration

This section provides information on configuring Agentic Security to suit your needs.

## Default Configuration

The default configuration file is `agesec.toml`. It includes settings for:

- General settings
- Module configurations
- Thresholds

## Customizing Configuration

1. Open the `agesec.toml` file in a text editor.
2. Modify the settings as needed. For example, to change the port:
   ```toml
   [modules.AgenticBackend.opts]
   port = 8718
   ```

## Advanced Configuration

For advanced configuration options, refer to the [API Reference](api_reference.md).
