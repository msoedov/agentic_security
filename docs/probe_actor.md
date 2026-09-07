# Probe actor

The `probe_actor` package runs scans against an LLM endpoint described by an
HTTP spec.

## Fuzzer

`agentic_security.probe_actor.fuzzer` is the scan engine:

- `generate_prompts` — yield prompts from a list or async source
- `get_modality_adapter` — wrap the spec for image or audio endpoints
- `process_prompt` / `process_prompt_batch` — send a prompt and score the reply
- `perform_single_shot_scan` — one prompt at a time
- `perform_many_shot_scan` — many-shot jailbreak conversations
- `scan_router` — pick the scan mode from configuration

`perform_single_shot_scan` is an async generator; it needs a request factory
(typically an `LLMSpec`) plus budget and dataset settings, not a bare prompt
string.

```python
from agentic_security.http_spec import LLMSpec
from agentic_security.probe_actor.fuzzer import perform_single_shot_scan

spec = LLMSpec.from_string(open("spec.http").read())
async for event in perform_single_shot_scan(spec, max_budget=1000):
    print(event)
```

## Refusal checks

There is no `check_refusal` helper. Use `refusal_heuristic(response)` in
`agentic_security.probe_actor.refusal`, which runs the detectors enabled under
`[detectors]` in `agentic_security.toml`.

```python
from agentic_security.probe_actor.refusal import refusal_heuristic

refusal_heuristic("I'm sorry, I can't help with that.")
```

See [refusal classifier plugins](refusal_classifier_plugins.md) to add a custom detector.
