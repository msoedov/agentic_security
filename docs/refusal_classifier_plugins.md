# Refusal classifier plugins

A detector examines the reply text of each response from the target (never the JSON envelope). If one or more enabled detectors return `True`, the scanner records a refusal for that prompt.

Phrase matching ignores case and treats typographic apostrophes (`’`) like ASCII ones.

## Built-in detectors

| Name | Default | Description |
| --- | --- | --- |
| `default` | on | Finds refusal phrases, for example "I'm sorry". |
| `ml_classifier` | off | A one-class SVM refusal classifier. Experimental: it has no measured accuracy yet. |
| `pii` | off | Finds personal data and credential leaks. |
| `sandbox_escape` | off | Finds Docker and Kubernetes sandbox-escape probes. |

To turn a detector on or off, set its name in the `[detectors]` section of `agentic_security.toml`:

```toml
[detectors]
default = true
ml_classifier = false
pii = true
sandbox_escape = false
```

## Make a custom detector

A detector is a class with the method `is_refusal(response: str) -> bool`.

```python
# my_package/detectors.py
class PhraseDetector:
    def __init__(self, phrases: list[str]):
        self.phrases = phrases

    def is_refusal(self, response: str) -> bool:
        return any(phrase in response for phrase in self.phrases)
```

You can also use the abstract base class `RefusalClassifierPlugin` from `agentic_security.probe_actor.refusal`.

## Enable a custom detector

Add a table to `[detectors]`. The tool imports the class and gives the `options` table to the constructor as keyword arguments.

```toml
[detectors.phrases]
class = "my_package.detectors:PhraseDetector"
enabled = true

[detectors.phrases.options]
phrases = ["I can't", "I won't"]
```

The class path can use the form `package.module:ClassName` or `package.module.ClassName`.

> **CAUTION:** The tool reads `[detectors]` one time, when it imports `agentic_security.probe_actor.refusal`. Restart the process after you change the section.

> **NOTE:** A new `RefusalClassifierManager()` that you make in code does not change the scan. The scan uses the manager that the tool builds from `[detectors]`. To build that manager from a different configuration, use `build_refusal_manager(config)`.

## Check a response in code

```python
from agentic_security.probe_actor.refusal import (
    pii_leak_heuristic,
    refusal_heuristic,
    sandbox_escape_heuristic,
)

refusal_heuristic("I'm sorry, I can't help with that.")  # True
pii_leak_heuristic("Contact me at jane@example.com")      # True
```

`pii_leak_heuristic` and `sandbox_escape_heuristic` always use their detector. They do not change the refusal result.

## PII detector

`PIIDetector` finds email addresses, US SSNs, phone numbers, private key blocks, and API tokens. It also finds credit card numbers that pass the Luhn check.

```python
from agentic_security.refusal_classifier import PIIDetector

detector = PIIDetector()
detector.detected_types(response)  # The names of the matched types.

# Credit card check off:
PIIDetector(detect_credit_cards=False)
```

To use only your patterns, give a tuple of `PIIPattern` objects as `patterns`. An empty tuple turns the pattern checks off.
