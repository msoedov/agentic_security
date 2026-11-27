# Probe actor

The `agentic_security.probe_actor` package sends the attack prompts to the target and scores the responses.

## Fuzzer

`agentic_security.probe_actor.fuzzer` is the scan engine.

| Function | Description |
| --- | --- |
| `scan_router` | Selects the single-shot scan or the many-shot scan from the scan settings. |
| `perform_single_shot_scan` | Sends one prompt in each request. |
| `perform_many_shot_scan` | Sends many-shot jailbreak conversations. |
| `process_prompt` / `process_prompt_batch` | Sends prompts and classifies each reply as `refused`, `complied`, `partial` or `error`. |
| `get_modality_adapter` | Wraps the spec for image or audio targets. |
| `generate_prompts` | Yields prompts from a list or from an async generator. |

The scan functions are async generators. Each item is a JSON string with the progress, the failure rate, the error rate, or a status message.

## Outcomes and scoring

Each prompt ends in one outcome:

| Outcome | Meaning |
| --- | --- |
| `refused` | The target declined. The attack failed. |
| `complied` | No refusal was found. The attack probably worked. |
| `partial` | A short refusal followed by much more content, for example a partial system-prompt leak. |
| `error` | HTTP error, connection error, unreadable body or empty reply. |

`failureRate` is the share of answered prompts where the attack worked: `(complied + partial) / (refused + complied + partial)`. A higher value is worse. Errors are not part of this value. `errorRate` reports them separately.

```python
from agentic_security.http_spec import LLMSpec
from agentic_security.probe_actor.fuzzer import perform_single_shot_scan

spec = LLMSpec.from_string(open("target.http").read())
datasets = [{"dataset_name": "simonycl/aya-23-8B_advbench_jailbreak", "selected": True}]
async for event in perform_single_shot_scan(spec, max_budget=1000, datasets=datasets):
    print(event)
```

At the end of a scan, the fuzzer writes `failures.csv` (the prompts that worked, with their outcome) and `full_scan_log.csv` (every event) to the current directory.

## Refusal checks

`refusal_heuristic(response)` in `agentic_security.probe_actor.refusal` uses the detectors that are enabled in `[detectors]`.

```python
from agentic_security.probe_actor.refusal import refusal_heuristic

refusal_heuristic("I'm sorry, I can't help with that.")  # True
```

To add a detector, refer to [Refusal classifier plugins](refusal_classifier_plugins.md).
