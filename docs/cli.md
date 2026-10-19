# CLI reference

The package installs two commands:

- `agentic_security` – the scanner. It has the subcommands `server`, `init`, `ls`, `ci`, and `scan`.
- `agesec` – the agent harness. Refer to [Agent harness](harness.md).

To show the help text, run:

```bash
agentic_security --help
```

If the command is not on your `PATH`, use `python -m agentic_security` instead.

## server

Starts the web UI and the API.

```bash
agentic_security server --host=127.0.0.1 --port=8718
```

| Option | Default | Description |
| --- | --- | --- |
| `--host` | `127.0.0.1` | The address that the server listens on. |
| `--port` | `8718` | The port that the server listens on. |

The short name is `s`.

## init

Creates `agentic_security.toml` in the current directory.

```bash
agentic_security init --host=127.0.0.1 --port=8718
```

The `--host` and `--port` values go into the example `llmSpec` and into `AgenticBackend.opts.port`. The short name is `i`.

> **CAUTION:** This command replaces an existing `agentic_security.toml`. Make a copy of your file before you run it.

## ls

Shows the dataset registry as a table. Use the names from this table in the `[modules]` section of the configuration.

```bash
agentic_security ls
```

## ci

Does a scan with the settings in `agentic_security.toml` from the current directory.

```bash
agentic_security ci
```

If the file is not there, the command stops with exit code 1. The command scans all modules in the `[modules]` section. It shows a table of results at the end.

> **CAUTION:** The `ci` command always exits with code 0 after a scan. This is also true when a module is above the threshold. To stop a pipeline when a module fails, use `scan`.

## scan

Does a scan without a configuration file. The command writes each result as one JSON line to stdout.

```bash
agentic_security scan --spec=target.http --max_th=0.3
cat target.http | agentic_security scan
```

| Option | Default | Description |
| --- | --- | --- |
| `--spec` | `-` | A file path, the HTTP spec as text, or `-` to read stdin. |
| `--max_budget` | `1000000` | The token budget for the scan. |
| `--max_th` | `0.3` | The failure-rate threshold (0 to 1). |
| `--optimize` | `False` | Stops a module early when its failure rate is high. |
| `--enable_multi_step_attack` | `False` | Adds many-shot attacks. |

The command scans all datasets in the registry. The exit code is 1 if one or more modules have a failure rate above `--max_th`. Otherwise, the exit code is 0.

## Local datasets

To add your prompts to a scan, refer to [Dataset extension](datasets.md).
