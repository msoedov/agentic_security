# CI/CD Integration

Integrate Agentic Security into your CI/CD pipeline to automate security scans.

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
2. Run the `agentic_security ci` command.

## Further Reading

For more details on CI/CD integration, refer to the [API Reference](api_reference.md).
