# Agent harness

The agent harness is the `agesec` command. It runs a scan one attempt at a time. An agent, a rule set, or a CI job decides the next action after each attempt. The harness and the `agentic_security` scanner are in the same package.

You must have Python 3.15 or newer. Install the package:

```sh
pip install 'agentic_security[harness]'
```

The `harness` extra does not add dependencies.

> **WARNING:** Use the harness only on targets that you have permission to test.

## Commands

```sh
agesec run --spec target.http --policy policy.json --decider rules --seed 42
agesec ls
agesec report RUN_ID -o report.json
agesec replay RUN_ID
agesec step RUN_ID
agesec decide RUN_ID --action continue --reason "try again"
```

| Command | Description |
| --- | --- |
| `run` | Starts a run. Writes events as JSON lines to stdout and diagnostics to stderr. |
| `ls` | Lists the runs with status, attempts, and cost. |
| `report` | Prints a JSON report. Writes it to `-o`, or to `report.json` in the run directory. |
| `replay` | Runs the decisions of a finished run again from the stored evidence. It does not send requests. |
| `step` | Does one attempt and prints the pending decision. |
| `decide` | Gives the decision for the pending attempt. |

`run` options: `--spec` (required), `--policy` (default `default`), `--decider` (`rules` or `jev`, default `rules`), `--seed` (default `0`), `--budget_usd`.

The harness keeps the log and the HTTP template (without expanded values) in `.agesec/runs/<id>/`. Use `${ENV_VAR}` for credentials in the spec.

## Exit codes

| Command | Code | Meaning |
| --- | --- | --- |
| `run`, `replay` (automated decider) | 0 | No findings. |
| | 1 | One or more findings. |
| | 2 | Error. |
| `run` (external decisions) | 0 | The run stopped after the first attempt. It waits for decisions. This code does not mean "no findings". |
| `step` | 3 | The run is finished. |
| `decide` | 2 | The action is not permitted. The log does not change. |

## Step-by-step decisions

1. Run `agesec step RUN_ID`. The harness does one attempt and prints one pending decision.
2. Run `agesec decide RUN_ID --action ACTION --reason REASON`.
3. Do steps 1 and 2 again until `step` exits with code 3.

If you run `step` again before `decide`, you get the same pending decision. The harness locks each run on POSIX systems. If a request stops before it is complete, the harness records an error when it continues. It does not send the request again.

## Actions

| Action | Result |
| --- | --- |
| `continue` | Tries the current tier again. |
| `escalate` | Goes to the next enabled tier. It skips disabled tiers. |
| `switch` | Goes to the next attack. |
| `stop` | Stops the run. |

## Policy

A policy is a JSON file. The names `default` (30 attempts) and `ci` (12 attempts) are built-in policies.

```json
{
  "max_attempts": 12,
  "max_per_tier": 2,
  "rate": 1.0,
  "sources": [
    {"kind": "dataset", "name": "deepset/prompt-injections", "limit": 100},
    {"kind": "csv", "name": "./attacks.csv", "limit": 50},
    {"kind": "module", "name": "my_attacks.sources:generate", "options": {"category": "injection"}, "limit": 20}
  ],
  "converters": [
    {"kind": "builtin", "name": "base64"},
    {"kind": "module", "name": "my_attacks.transforms:convert", "options": {}}
  ],
  "strategies": [{"kind": "builtin", "name": "transcript"}]
}
```

### Rules decider

The policy key `rules` maps each outcome (`refused`, `partial`, `complied`, `error`) to a list of actions. The decider uses the first permitted action in the list. The harness removes the actions that the attempt limits or the budget do not permit.

### jev decider

The `jev` decider uses an LLM through [OpenRouter chat completions](https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request).

1. Set the `OPENROUTER_API_KEY` environment variable.
2. Set `jev_model` in the policy.

The harness applies the same policy checks to `jev` decisions. If the remote call fails, the harness does not use the rules decider.

## Sources

A policy selects sources and techniques. It does not contain prompts.

| Kind | Description |
| --- | --- |
| `dataset` | A name from the `probe_data` registry. The harness uses the registry loader. `harness/smoke` is a small offline CSV dataset. The `default` and `ci` policies use it. |
| `csv` | A local CSV file with a `prompt` column. The path is relative to the policy file. |
| `module` | A Python callable that is installed: `package.module:name`. |

`limit` sets the maximum number of prompts from each source. A dataset loader can load the full dataset before the harness applies the limit.

> **CAUTION:** If a source is unknown, empty, or not valid, the run does not start. The harness does not continue with fewer sources.

## Converters and strategies

The built-in converters are `base64` and `fictional`. The built-in multi-turn strategy is `transcript`. It adds the recent responses to the prompt as a text conversation, for HTTP specs that accept one prompt.

The harness uses the converters and the strategies in their list order. A `continue` action goes to the next item. An empty list disables that tier.

## Python extensions

A `module` reference is a trusted local extension. The harness does not install modules.

- A source callable has the signature `generate(*, options: dict, seed: int)`. It returns an iterable of prompt strings that are not empty, or a `ProbeDataset`.
- A converter or strategy callable has the signature `convert(*, prompt: str, history: list[dict], options: dict, seed: int)`. It returns one prompt string that is not empty. `history` has the recent attempts for the attack.

These callables are synchronous. They must only make prompts. The harness sends the requests, so the budget, the log, the classification, and the rate limits apply.

Some legacy modules run a full scanner, for example the Garak subprocess. They are not prompt generators. To use them, wrap the prompt API of the third-party tool in this interface.

The harness does not count network costs of an extension.

The run stores the resolved prompts and the source configuration. Each attempt records its technique and options. `replay` does not import extensions or load datasets again.

## Budget

A dollar budget (`--budget_usd`) needs positive `request_cost_usd` values. The `jev` decider also needs `decision_cost_usd`. The harness does not send a call that is more than the remaining budget.

> **NOTE:** These values are estimates. The provider does not enforce them. If you do not give estimates, the harness counts the costs as zero and marks them as estimated.

## Report

`agesec report` prints a JSON report. The Python function `build_report(log)` returns a `Report` dataclass. The report has:

- Status, exit code (`null` until the run is finished), and stop reason.
- Outcome counts, cost, and duration.
- Findings, attack sources, transformations, and decision trails.
- The original events.

The harness does not make HTML, XML, or JUnit reports. An agent or a CI job can use the JSON report directly.

> **CAUTION:** The evidence in the report is untrusted content. Escape it before you show it in a UI.

## Findings

A finding is a signal from the refusal classifier. A person must examine it. A finding does not prove that the attack goal was reached.

The OWASP mappings show the objective of the attack: [LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) and [ASI01](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/). The harness does not test the full OWASP Top 10.

## Integrations

| Tool | Location |
| --- | --- |
| Claude plugin | `integrations/claude` |
| Codex | `integrations/codex/AGENTS.md` and `integrations/codex/skills` |
| CI example | `.github/workflows/harness-example.yml` |

The CI example starts only when you trigger it manually. It uses a localhost target. For a hosted CI system, replace the target with an HTTP spec that you have permission to test.
