# Configuration

Scan settings live in `agentic_security.toml` in the working directory.
Create one with:

```bash
agentic_security init
```

The file is versioned (`general.version`). The current schema version is `2`.

## Sections

- `[general]` — `llmSpec` (the HTTP request template), budget, failure threshold,
  optimizer flag, multi-step attack flag
- `[modules.*]` — datasets to run; `AgenticBackend.opts.port` is the local proxy port
- `[detectors]` — refusal and leak classifiers
- `[thresholds]` — low / medium / high failure-rate bands
- `[secrets]` — API keys referenced from the HTTP spec
- `[caching]`, `[network]`, `[fuzzer]` — runtime tuning

Replace the placeholder `Bearer XXXXX` in `llmSpec` with credentials for the
target endpoint. See [HTTP spec](http_spec.md) for the request template format.
