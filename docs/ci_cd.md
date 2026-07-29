# CI/CD Integration

Integrate Agentic Security into your CI/CD pipeline to automate security scans.

## Stateless scans

Use `scan` when an agent or CI job needs a one-shot scan without starting the
web server or creating `agentic_security.toml`:

```shell
agentic_security scan \
  --spec target.http \
  --dataset deepset/prompt-injections \
  --max-budget 1000 \
  --max-th 0.3
```

`--spec` accepts an HTTP spec directly, a file path, or `-` for standard input.
`--dataset` accepts one registry name or a comma-separated list. Run
`agentic_security ls` to see the registry.

The command writes JSON Lines to standard output and diagnostics to standard
error. It does not create CSV files unless `--artifacts-dir` is supplied.

Exit codes are:

- `0`: the scan completed within the failure-rate threshold
- `1`: at least one module exceeded the threshold
- `2`: the input was invalid or the scan failed

## GitHub Actions

Use the provided GitHub Action workflow to perform automated scans:

```yaml
name: Security Scan

on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install agentic_security
      - name: Run security scan
        run: agentic_security ci
```

## Custom CI/CD Pipelines

For custom pipelines, ensure the following steps:

1. Install dependencies.
1. Run the `agentic_security ci` command.

## Further Reading

For more details on CI/CD integration, refer to the [API Reference](api_reference.md).
