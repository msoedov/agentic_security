# Design

This page shows the main parts of Agentic Security and the flow of a scan.

## Parts

| Part | Package | Function |
| --- | --- | --- |
| CLI | `agentic_security.__main__` | Starts the server or a scan. |
| Web server | `agentic_security.app`, `agentic_security.routes` | Gives the UI and the scan API. |
| Scanner | `agentic_security.lib` | Reads the configuration and shows the results table. |
| HTTP spec | `agentic_security.http_spec` | Parses the request template and sends the requests. |
| Probe data | `agentic_security.probe_data` | Loads datasets, transforms prompts, makes images and audio. |
| Probe actor | `agentic_security.probe_actor` | Sends the prompts and scores the responses. |
| Detectors | `agentic_security.refusal_classifier` | Find refusals and leaks in the responses. |
| Agent harness | `agentic_security_harness` | Runs a scan step by step for an agent or for CI. |

## Scan flow

1. The CLI or the web server gets the HTTP spec and the list of datasets.
2. `LLMSpec.from_string` parses the HTTP spec.
3. `prepare_prompts` loads the selected datasets and adds the transformed datasets.
4. `scan_router` selects the single-shot scan or the many-shot scan.
5. For each prompt, the fuzzer puts the prompt in the spec and sends the request.
6. The detectors examine the response. The fuzzer counts the prompt as a failure if a detector finds a refusal. A request error or a response that is not JSON is also a failure.
7. The fuzzer sends the failure rate of each module as a JSON line. The failure rate is the failures divided by the prompts sent.
8. At the end, the fuzzer writes `failures.csv` and `full_scan_log.csv`.
9. The CLI shows a table. A module with a failure rate above `max_th` has the status FAIL.

## Extension points

| To add | Refer to |
| --- | --- |
| Prompts from a CSV file | [Dataset extension](datasets.md) |
| A dataset in the registry | [Dataset extension](datasets.md) |
| A prompt generator | [External modules](external_module.md) |
| A detector | [Refusal classifier plugins](refusal_classifier_plugins.md) |
| A harness source or converter | [Agent harness](harness.md) |
