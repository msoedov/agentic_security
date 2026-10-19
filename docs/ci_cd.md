# CI/CD integration

You can do a scan in a CI pipeline with the `scan` command or the `ci` command.

| Command | Datasets | Exit code |
| --- | --- | --- |
| `agentic_security scan` | All datasets in the registry. | 1 if a module is above `--max_th`. Otherwise 0. |
| `agentic_security ci` | The `[modules]` in `agentic_security.toml`. | Always 0 after a scan. |

> **CAUTION:** The `ci` command does not stop the pipeline when a module fails. To stop the pipeline, use `scan`.

> **WARNING:** Do a scan only on endpoints that you have permission to test.

## GitHub Actions

This example stops the pipeline when a module has a failure rate above 30%.

```yaml
name: Security scan

on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.15"
      - run: pip install agentic_security
      - run: agentic_security scan --spec=target.http --max_th=0.3
```

Keep `target.http` in the repository. Do not put credentials in the file. Refer to [HTTP spec](http_spec.md).

## Other CI systems

1. Install Python 3.15 or newer.
2. Run `pip install agentic_security`.
3. Run `agentic_security scan --spec=target.http`.
4. Use the exit code to set the result of the job.

## Agent harness in CI

The workflow `.github/workflows/harness-example.yml` shows the `agesec` harness in CI. Refer to [Agent harness](harness.md).
