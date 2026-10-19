# Configuration

The `ci` command and the web server read `agentic_security.toml` from the current directory. To create the file, run:

```bash
agentic_security init
```

The schema version is `2`. If `general.version` has a different value, the tool shows an error.

## [general]

| Key | Default | Description |
| --- | --- | --- |
| `llmSpec` | self-probe request | The HTTP request for the target. Refer to [HTTP spec](http_spec.md). |
| `maxBudget` | `1000000` | The token budget for the scan. |
| `max_th` | `0.3` | The failure-rate threshold (0 to 1). A module above this value has the status FAIL. |
| `optimize` | `false` | Stops a module early when its failure rate is high. Refer to [Early stop](optimizer.md). |
| `enableMultiStepAttack` | `false` | Adds many-shot attacks. |
| `version` | `2` | The schema version. |

Replace the `Bearer XXXXX` value in `llmSpec` with the credentials for your endpoint.

## [modules.NAME]

Each table is one dataset to scan. Get the dataset names from `agentic_security ls`.

```toml
[modules.aya-23-8B_advbench_jailbreak]
dataset_name = "simonycl/aya-23-8B_advbench_jailbreak"

[modules.AgenticBackend]
dataset_name = "AgenticBackend"
[modules.AgenticBackend.opts]
port = 8718
modules = ["encoding"]
```

The `opts` table goes to the dataset module. Each module has different options.

## [detectors]

The detectors examine each response from the target.

| Key | Default | Description |
| --- | --- | --- |
| `default` | `true` | Finds refusal phrases. |
| `ml_classifier` | `true` | A one-class SVM refusal classifier. |
| `pii` | `false` | Finds personal data and credential leaks. |
| `sandbox_escape` | `false` | Finds Docker and Kubernetes sandbox-escape probes. |

To add a custom detector, refer to [Refusal classifier plugins](refusal_classifier_plugins.md).

## [thresholds]

The `init` command writes the values `low`, `medium`, and `high` (defaults `0.15`, `0.3`, `0.5`).

> **NOTE:** The code does not read this section at this time. Use `general.max_th` to set the pass/fail threshold.

## [secrets]

Each key is a secret name. A value that starts with `$` is the name of an environment variable.

```toml
[secrets]
OPENAI_API_KEY = "$OPENAI_API_KEY"
```

When the web server starts a scan, it replaces `$OPENAI_API_KEY` in the body of `llmSpec` with the secret value.

> **NOTE:** The tool does not replace secret names in the request line or in the headers. Put the credential value in the header yourself.

## [caching]

The `init` command writes the keys `enable`, `cache_size`, and `use_disk_cache`.

> **NOTE:** The code does not read this section at this time. To change the disk cache directory, set the `AGENTIC_SECURITY_CACHE_DIR` or `DISK_CACHE_DIR` environment variable. The default directory is `.cache/agentic_security` in the current directory.

## [network]

| Key | Default | Description |
| --- | --- | --- |
| `retry` | `3` | The number of retries for each request. |
| `timeout_connect` | `30` | The connection timeout in seconds. |
| `timeout_response` | `90` | The response timeout in seconds. |

## [fuzzer]

| Key | Default | Description |
| --- | --- | --- |
| `max_prompt_length` | `2048` | The maximum prompt length in the scan results. The `init` command writes the old spelling `max_prompt_lenght`. The code reads the two names. |
| `budget_multiplier` | `100000000` | The multiplier for the token budget. |
| `initial_optimizer_points` | `25` | The random points before the optimizer fits a model. |
| `min_failure_samples` | `5` | The minimum samples before an early stop. |
| `failure_rate_threshold` | `0.5` | The failure rate that causes an early stop. |
