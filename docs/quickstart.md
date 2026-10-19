# Quickstart

This procedure starts the web UI and does a scan from the command line.

## Install the package

```shell
pip install agentic_security
```

## Start the web UI

```shell
agentic_security server
```

Open `http://127.0.0.1:8718` in a web browser.

> **NOTE:** The `agentic_security` command without a subcommand does not start the server. It shows the help text.

## Do a scan from the command line

1. Create the configuration file `agentic_security.toml`:

    ```shell
    agentic_security init
    ```

2. Open `agentic_security.toml`.
3. Replace the example `llmSpec` with the HTTP request for your endpoint. Refer to [HTTP spec](http_spec.md).
4. Show the available datasets:

    ```shell
    agentic_security ls
    ```

5. Add the datasets that you want to the `[modules]` section.
6. Start the scan:

    ```shell
    agentic_security ci
    ```

The scan shows a table with the failure rate for each module.

## Next steps

- [CLI reference](cli.md)
- [Configuration](configuration.md)
- [CI/CD integration](ci_cd.md)
